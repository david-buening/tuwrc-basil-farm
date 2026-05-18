#include "lerobot_hardware/so101_hardware_interface.hpp"

#include <chrono>
#include <cstring>
#include <fcntl.h>
#include <termios.h>
#include <unistd.h>

#include "hardware_interface/types/hardware_interface_type_values.hpp"
#include "pluginlib/class_list_macros.hpp"

// STS3215 register addresses
static constexpr uint8_t REG_GOAL_POSITION_L  = 0x2A;  // 42
static constexpr uint8_t REG_PRESENT_POSITION_L = 0x38; // 56

// SCS instruction codes
static constexpr uint8_t INSTR_PING  = 0x01;
static constexpr uint8_t INSTR_READ  = 0x02;
static constexpr uint8_t INSTR_WRITE = 0x03;

namespace lerobot_hardware
{

// ---------------------------------------------------------------------------
// Lifecycle callbacks
// ---------------------------------------------------------------------------

hardware_interface::CallbackReturn SO101HardwareInterface::on_init(
  const hardware_interface::HardwareInfo & info)
{
  if (hardware_interface::SystemInterface::on_init(info) !=
    hardware_interface::CallbackReturn::SUCCESS)
  {
    return hardware_interface::CallbackReturn::ERROR;
  }

  // Read hardware parameters from URDF
  if (info_.hardware_parameters.count("serial_port")) {
    serial_port_ = info_.hardware_parameters.at("serial_port");
  }
  if (info_.hardware_parameters.count("baud_rate")) {
    baud_rate_ = std::stoi(info_.hardware_parameters.at("baud_rate"));
  }

  n_joints_ = info_.joints.size();
  hw_positions_.assign(n_joints_, 0.0);
  hw_commands_.assign(n_joints_, 0.0);
  servo_ids_.resize(n_joints_);

  // Map joint name (e.g. "1", "2", ...) directly to servo ID
  for (std::size_t i = 0; i < n_joints_; ++i) {
    try {
      servo_ids_[i] = static_cast<uint8_t>(std::stoul(info_.joints[i].name));
    } catch (...) {
      RCLCPP_ERROR(rclcpp::get_logger("SO101HardwareInterface"),
        "Joint name '%s' is not a valid servo ID (expected integer 1–6).",
        info_.joints[i].name.c_str());
      return hardware_interface::CallbackReturn::ERROR;
    }
  }

  RCLCPP_INFO(rclcpp::get_logger("SO101HardwareInterface"),
    "Initialised for %zu joints on %s @ %d baud.",
    n_joints_, serial_port_.c_str(), baud_rate_);

  return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn SO101HardwareInterface::on_configure(
  const rclcpp_lifecycle::State & /*previous_state*/)
{
  if (!open_serial(serial_port_, baud_rate_)) {
    RCLCPP_ERROR(rclcpp::get_logger("SO101HardwareInterface"),
      "Failed to open serial port %s.", serial_port_.c_str());
    return hardware_interface::CallbackReturn::ERROR;
  }
  RCLCPP_INFO(rclcpp::get_logger("SO101HardwareInterface"),
    "Serial port %s opened.", serial_port_.c_str());
  return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn SO101HardwareInterface::on_activate(
  const rclcpp_lifecycle::State & /*previous_state*/)
{
  // Verify all servos respond, then seed command targets from current positions
  for (std::size_t i = 0; i < n_joints_; ++i) {
    if (!ping(servo_ids_[i])) {
      RCLCPP_WARN(rclcpp::get_logger("SO101HardwareInterface"),
        "Servo %d did not respond to ping — continuing anyway.", servo_ids_[i]);
    }

    int16_t steps = 0;
    if (read_position(servo_ids_[i], steps)) {
      hw_positions_[i] = (steps - STEPS_CENTER) / STEPS_PER_RAD;
    }
    hw_commands_[i] = hw_positions_[i];
  }

  RCLCPP_INFO(rclcpp::get_logger("SO101HardwareInterface"), "Hardware activated.");
  return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn SO101HardwareInterface::on_deactivate(
  const rclcpp_lifecycle::State & /*previous_state*/)
{
  RCLCPP_INFO(rclcpp::get_logger("SO101HardwareInterface"), "Hardware deactivated.");
  return hardware_interface::CallbackReturn::SUCCESS;
}

// ---------------------------------------------------------------------------
// Interface exports
// ---------------------------------------------------------------------------

std::vector<hardware_interface::StateInterface>
SO101HardwareInterface::export_state_interfaces()
{
  std::vector<hardware_interface::StateInterface> interfaces;
  for (std::size_t i = 0; i < n_joints_; ++i) {
    interfaces.emplace_back(
      info_.joints[i].name,
      hardware_interface::HW_IF_POSITION,
      &hw_positions_[i]);
  }
  return interfaces;
}

std::vector<hardware_interface::CommandInterface>
SO101HardwareInterface::export_command_interfaces()
{
  std::vector<hardware_interface::CommandInterface> interfaces;
  for (std::size_t i = 0; i < n_joints_; ++i) {
    interfaces.emplace_back(
      info_.joints[i].name,
      hardware_interface::HW_IF_POSITION,
      &hw_commands_[i]);
  }
  return interfaces;
}

// ---------------------------------------------------------------------------
// read / write
// ---------------------------------------------------------------------------

hardware_interface::return_type SO101HardwareInterface::read(
  const rclcpp::Time & /*time*/, const rclcpp::Duration & /*period*/)
{
  for (std::size_t i = 0; i < n_joints_; ++i) {
    int16_t steps = 0;
    if (read_position(servo_ids_[i], steps)) {
      hw_positions_[i] = (steps - STEPS_CENTER) / STEPS_PER_RAD;
    } else {
      RCLCPP_WARN_THROTTLE(rclcpp::get_logger("SO101HardwareInterface"),
        *rclcpp::Clock::make_shared(), 2000,
        "Read failed for servo %d — using last known position.", servo_ids_[i]);
    }
  }
  return hardware_interface::return_type::OK;
}

hardware_interface::return_type SO101HardwareInterface::write(
  const rclcpp::Time & /*time*/, const rclcpp::Duration & /*period*/)
{
  for (std::size_t i = 0; i < n_joints_; ++i) {
    int steps_raw = static_cast<int>(hw_commands_[i] * STEPS_PER_RAD) + STEPS_CENTER;
    uint16_t steps = static_cast<uint16_t>(std::clamp(steps_raw, 0, STEPS_MAX));

    if (!write_position(servo_ids_[i], steps)) {
      RCLCPP_WARN_THROTTLE(rclcpp::get_logger("SO101HardwareInterface"),
        *rclcpp::Clock::make_shared(), 2000,
        "Write failed for servo %d.", servo_ids_[i]);
    }
  }
  return hardware_interface::return_type::OK;
}

// ---------------------------------------------------------------------------
// Serial helpers
// ---------------------------------------------------------------------------

bool SO101HardwareInterface::open_serial(const std::string & port, int baud_rate)
{
  fd_ = ::open(port.c_str(), O_RDWR | O_NOCTTY | O_NONBLOCK);
  if (fd_ < 0) {
    return false;
  }

  // Switch to blocking mode
  int flags = fcntl(fd_, F_GETFL, 0);
  fcntl(fd_, F_SETFL, flags & ~O_NONBLOCK);

  struct termios tty{};
  if (tcgetattr(fd_, &tty) != 0) {
    close_serial();
    return false;
  }

  // 8N1, no flow control, raw mode
  tty.c_cflag &= ~(PARENB | CSTOPB | CSIZE | CRTSCTS);
  tty.c_cflag |= CS8 | CREAD | CLOCAL;
  tty.c_lflag &= ~(ICANON | ECHO | ECHOE | ECHONL | ISIG);
  tty.c_iflag &= ~(IXON | IXOFF | IXANY | IGNBRK | BRKINT | PARMRK |
                    ISTRIP | INLCR | IGNCR | ICRNL);
  tty.c_oflag &= ~(OPOST | ONLCR);

  // Non-blocking reads with 10 ms inter-character timeout
  tty.c_cc[VTIME] = 1;
  tty.c_cc[VMIN]  = 0;

  // Set baud rate — B1000000 is available on Linux for 1 Mbaud
  speed_t speed = B1000000;
  if (baud_rate == 115200)  speed = B115200;
  else if (baud_rate == 57600)   speed = B57600;
  else if (baud_rate == 1000000) speed = B1000000;

  cfsetispeed(&tty, speed);
  cfsetospeed(&tty, speed);

  if (tcsetattr(fd_, TCSANOW, &tty) != 0) {
    close_serial();
    return false;
  }

  tcflush(fd_, TCIOFLUSH);
  usleep(100000);  // let the USB-serial converter settle
  return true;
}

void SO101HardwareInterface::close_serial()
{
  if (fd_ >= 0) {
    ::close(fd_);
    fd_ = -1;
  }
}

bool SO101HardwareInterface::read_bytes(uint8_t * buf, size_t len, int timeout_ms)
{
  auto deadline = std::chrono::steady_clock::now() +
    std::chrono::milliseconds(timeout_ms);
  std::size_t received = 0;

  while (received < len) {
    if (std::chrono::steady_clock::now() > deadline) {
      return false;
    }
    ssize_t n = ::read(fd_, buf + received, len - received);
    if (n > 0) {
      received += static_cast<std::size_t>(n);
    } else if (n < 0 && errno != EAGAIN) {
      return false;
    }
  }
  return true;
}

// ---------------------------------------------------------------------------
// SCS/STS protocol helpers
// ---------------------------------------------------------------------------
//
// Packet format:
//   TX  0xFF 0xFF  ID  LEN  INSTR  [PARAMS...]  CHK
//   RX  0xFF 0xFF  ID  LEN  ERROR  [DATA...]    CHK
//   CHK = (~(ID + LEN + INSTR + sum(params))) & 0xFF
// ---------------------------------------------------------------------------

bool SO101HardwareInterface::ping(uint8_t servo_id)
{
  tcflush(fd_, TCIOFLUSH);

  uint8_t chk = static_cast<uint8_t>(~(servo_id + 0x02 + INSTR_PING) & 0xFF);
  uint8_t pkt[] = {0xFF, 0xFF, servo_id, 0x02, INSTR_PING, chk};
  if (::write(fd_, pkt, sizeof(pkt)) != static_cast<ssize_t>(sizeof(pkt))) {
    return false;
  }

  uint8_t rsp[6];
  return read_bytes(rsp, sizeof(rsp), 20) &&
         rsp[0] == 0xFF && rsp[1] == 0xFF && rsp[2] == servo_id;
}

bool SO101HardwareInterface::read_position(uint8_t servo_id, int16_t & position_steps)
{
  tcflush(fd_, TCIOFLUSH);

  // TX: FF FF ID 04 02 REG_PRESENT_POSITION_L 02 CHK
  uint8_t chk = static_cast<uint8_t>(
    ~(servo_id + 0x04 + INSTR_READ + REG_PRESENT_POSITION_L + 0x02) & 0xFF);
  uint8_t pkt[] = {0xFF, 0xFF, servo_id, 0x04, INSTR_READ,
                   REG_PRESENT_POSITION_L, 0x02, chk};

  if (::write(fd_, pkt, sizeof(pkt)) != static_cast<ssize_t>(sizeof(pkt))) {
    return false;
  }

  // RX: FF FF ID 04 ERR POS_L POS_H CHK  (8 bytes)
  uint8_t rsp[8];
  if (!read_bytes(rsp, sizeof(rsp), 20)) {
    return false;
  }
  if (rsp[0] != 0xFF || rsp[1] != 0xFF || rsp[2] != servo_id) {
    return false;
  }

  // STS3215 returns position as little-endian 16-bit
  uint16_t raw = static_cast<uint16_t>(rsp[5]) |
                 (static_cast<uint16_t>(rsp[6]) << 8);
  position_steps = static_cast<int16_t>(raw);
  return true;
}

bool SO101HardwareInterface::write_position(uint8_t servo_id, uint16_t position_steps)
{
  // TX: FF FF ID 05 03 REG_GOAL_POSITION_L POS_L POS_H CHK
  uint8_t pos_l = position_steps & 0xFF;
  uint8_t pos_h = (position_steps >> 8) & 0xFF;
  uint8_t chk = static_cast<uint8_t>(
    ~(servo_id + 0x05 + INSTR_WRITE + REG_GOAL_POSITION_L + pos_l + pos_h) & 0xFF);
  uint8_t pkt[] = {0xFF, 0xFF, servo_id, 0x05, INSTR_WRITE,
                   REG_GOAL_POSITION_L, pos_l, pos_h, chk};

  // No response expected (or we discard it to keep the bus clean)
  return ::write(fd_, pkt, sizeof(pkt)) == static_cast<ssize_t>(sizeof(pkt));
}

}  // namespace lerobot_hardware

PLUGINLIB_EXPORT_CLASS(
  lerobot_hardware::SO101HardwareInterface,
  hardware_interface::SystemInterface)
