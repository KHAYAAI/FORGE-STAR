#include "Components/ModeManager/ModeManager.hpp"
#include "FpConfig.hpp"

namespace ForgeSat {

ModeManager::ModeManager(const char* const compName)
    : ModeManagerComponentBase(compName), m_safe(false), m_volts(0.0f), m_sinceReport(0) {}

ModeManager::~ModeManager() {}

void ModeManager::enterSafe(const char* reason) {
    if (this->m_safe) {
        return;
    }
    this->m_safe = true;
    Fw::LogStringArg r(reason);
    this->log_WARNING_HI_EnteredSafe(r);
    if (this->isConnected_modeOut_OutputPort(0)) {
        this->modeOut_out(0, true);
    }
    this->tlmWrite_Safe(true);
}

void ModeManager::schedIn_handler(FwIndexType portNum, U32 context) {
    if (++this->m_sinceReport > POWER_TIMEOUT_TICKS) {
        this->enterSafe("no bus power report");
    }
    this->tlmWrite_Safe(this->m_safe);
    this->tlmWrite_BusVolts(this->m_volts);
}

void ModeManager::busPowerIn_handler(FwIndexType portNum, F32 volts) {
    this->m_volts = volts;
    this->m_sinceReport = 0;
    if (volts < SAFE_BELOW_V) {
        this->enterSafe("low bus voltage");
    }
}

void ModeManager::MM_SAFE_cmdHandler(FwOpcodeType opCode, U32 cmdSeq) {
    this->enterSafe("operator command");
    this->cmdResponse_out(opCode, cmdSeq, Fw::CmdResponse::OK);
}

void ModeManager::MM_NOMINAL_cmdHandler(FwOpcodeType opCode, U32 cmdSeq) {
    if (this->m_volts < NOMINAL_ABOVE_V) {
        this->log_WARNING_LO_NominalRefused(this->m_volts);
        this->cmdResponse_out(opCode, cmdSeq, Fw::CmdResponse::EXECUTION_ERROR);
        return;
    }
    if (this->m_safe) {
        this->m_safe = false;
        this->log_ACTIVITY_HI_ExitedSafe();
        if (this->isConnected_modeOut_OutputPort(0)) {
            this->modeOut_out(0, false);
        }
    }
    this->tlmWrite_Safe(false);
    this->cmdResponse_out(opCode, cmdSeq, Fw::CmdResponse::OK);
}

}  // namespace ForgeSat
