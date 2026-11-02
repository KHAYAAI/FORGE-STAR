// ======================================================================
// \title  PayloadSim.hpp
// \brief  Hardware stand-in for running the payload flight software on a host or dev board
// ======================================================================
#ifndef ForgeSat_PayloadSim_HPP
#define ForgeSat_PayloadSim_HPP

#include <cstdio>
#include "Components/PayloadSim/PayloadSimComponentAc.hpp"

namespace ForgeSat {

class PayloadSim : public PayloadSimComponentBase {
  public:
    explicit PayloadSim(const char* const compName);
    ~PayloadSim();

    //! messagesPerTick: device messages per 1 Hz tick; passPeriod/passLength in ticks (seconds)
    void configure(const char* downlinkPath, U32 messagesPerTick, U32 passPeriod, U32 passLength);

  PRIVATE:
    void schedIn_handler(FwIndexType portNum, U32 context) override;
    void linkIn_handler(FwIndexType portNum, Fw::Buffer& fwBuffer) override;

    FILE* m_file;
    U32 m_perTick, m_period, m_length;
    U32 m_tick, m_generated, m_bytes;
    bool m_pass;
};

}  // namespace ForgeSat
#endif
