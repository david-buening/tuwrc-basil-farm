#pragma once

#include <cmath>
#include <string>
#include <vector>

#include "hardware_interface/system_interface.hpp"
#include "hardware_interface/types/hardware_interface_return_values.hpp"
#include "rclcpp/rclcpp.hpp"
#include "rclcpp_lifecycle/state.hpp"

namespace lerobot_hardware
{

class SO101HardwareInterface : public hardware_interface::SystemInterface
{
public:
  RCLCPP_SHARED_PTR_DEFINITIONS(SO101HardwareInterface)

  hardware_interface::CallbackReturn on_init(
    const hardware_interface::HardwareInfo & info) override;

  hardware_interface::CallbackReturn on_configure(
    const rclcpp_lifecycle::State & previous_state) override;

  hardware_interface::CallbackReturn on_activate(
    const rclcpp_lifecycle::State & previous_state) override;

  hardware_interface::CallbackReturn on_deactivate(
    const rclcpp_lifecycle::State & previous_state) override;

  std::vector<hardware_interface::StateInterface> export_state_interfaces() override;
  std::vector<hardware_interface::CommandInterface> export_command_interfaces() override;

  hardware_interface::return_type read(
    const rclcpp::Time & time, const rclcpp::Duration & period) override;

  hardware_interface::return_type write(
    const rclcpp::Time & time, const rclcpp::Duration & period) override;

private:
  bool open_serial(const std::string & port, int baud_rate);
  void close_serial();
  bool read_bytes(uint8_t * buf, size_t len, int timeout_ms);
  bool read_position(uint8_t servo_id, int16_t & position_steps);
  bool write_position(uint8_t servo_id, uint16_t position_steps);
  bool ping(uint8_t servo_id);

  int fd_{-1};
  std::string serial_port_{"/dev/ttyUSB0"};
  int baud_rate_{1000000};

  std::size_t n_joints_{0};
  std::vector<uint8_t> servo_ids_;
  std::vector<double> hw_positions_;
  std::vector<double> hw_commands_;

  // STS3215: 4096 steps per revolution, center (0 rad) at step 2048
  static constexpr double STEPS_PER_RAD = 4096.0 / (2.0 * M_PI);
  static constexpr int STEPS_CENTER = 2048;
  static constexpr int STEPS_MAX = 4095;
};

}  // namespace lerobot_hardware
