// ======================================================================
// \title  PayloadSim.cpp
// ======================================================================
#include "Components/PayloadSim/PayloadSim.hpp"
#include "FpConfig.hpp"
#include "forge.h"

namespace ForgeSat {

static const char* const KINDS[] = {"pump", "soil", "collar", "vessel", "tracker"};

PayloadSim::PayloadSim(const char* const compName)
    : PayloadSimComponentBase(compName), m_file(nullptr), m_perTick(2), m_period(60), m_length(10),
      m_tick(0), m_generated(0), m_bytes(0), m_pass(false) {}

PayloadSim::~PayloadSim() {
    if (this->m_file) {
        std::fclose(this->m_file);
    }
}

void PayloadSim::configure(const char* path, U32 perTick, U32 period, U32 length) {
    this->m_perTick = perTick;
    this->m_period = period;
    this->m_length = length;
    this->m_file = std::fopen(path, "wb");
    Fw::LogStringArg p(path);
    this->log_ACTIVITY_HI_DownlinkFile(p);
}

void PayloadSim::schedIn_handler(FwIndexType portNum, U32 context) {
    const U32 now = this->getTime().getSeconds();
    // device messages: same naming as ground/simulator so the gateway registry recognises them
    for (U32 i = 0; i < this->m_perTick; i++) {
        const U32 n = this->m_generated++;
        char name[24];
        std::snprintf(name, sizeof name, "%s-%04u", KINDS[n % 5], static_cast<unsigned>(n % 50));
        char json[64];
        std::snprintf(json, sizeof json, "{\"seq\":%u,\"battery_v\":%u.%02u}", static_cast<unsigned>(n),
                      3u + (n % 2), static_cast<unsigned>(n % 100));
        Fw::String payload(json);
        if (this->isConnected_deviceOut_OutputPort(0)) {
            this->deviceOut_out(0, forge_short_id(name), now, -2550000 + static_cast<I32>(n % 400) * 1000,
                                2800000 + static_cast<I32>(n % 300) * 1000, payload);
        }
    }
    // pass schedule: gateway in view for m_length out of every m_period ticks
    const bool pass = (this->m_tick % this->m_period) >= (this->m_period - this->m_length);
    if (pass != this->m_pass) {
        this->m_pass = pass;
        if (this->isConnected_passOut_OutputPort(0)) {
            this->passOut_out(0, pass);
        }
    }
    this->m_tick++;
    this->tlmWrite_MessagesGenerated(this->m_generated);
    this->tlmWrite_BytesDownlinked(this->m_bytes);
    this->tlmWrite_PassActive(this->m_pass);
}

void PayloadSim::linkIn_handler(FwIndexType portNum, Fw::Buffer& fwBuffer) {
    if (this->m_file) {
        std::fwrite(fwBuffer.getData(), 1, fwBuffer.getSize(), this->m_file);
        std::fflush(this->m_file);
    }
    this->m_bytes += fwBuffer.getSize();
}

}  // namespace ForgeSat
