// ======================================================================
// \title  CmdAuth.cpp
// ======================================================================
#include "Components/CmdAuth/CmdAuth.hpp"
#include "FpConfig.hpp"
#include "forge_auth.h"
#include <cstdlib>
#include <cstring>

namespace ForgeSat {

CmdAuth::CmdAuth(const char* const compName)
    : CmdAuthComponentBase(compName), m_keyLen(0), m_encrypted(true), m_last(0), m_accepted(0), m_rejected(0) {
    std::memset(this->m_key, 0, sizeof this->m_key);
}

CmdAuth::~CmdAuth() {}

void CmdAuth::configure(const U8* key, U32 len, U32 lastCounter) {
    this->m_keyLen = len > sizeof this->m_key ? static_cast<U32>(sizeof this->m_key) : len;
    std::memcpy(this->m_key, key, this->m_keyLen);
    forge_auth_derive(this->m_key, this->m_keyLen, this->m_kEnc, this->m_kMac);
    const char* enc = std::getenv("FORGE_CMD_ENCRYPT");
    this->m_encrypted = !(enc && enc[0] == '0');
    this->m_last = lastCounter;
    this->log_ACTIVITY_HI_KeyLoaded(this->m_keyLen);
}

void CmdAuth::configureFromHexEnv(const char* envName) {
    const char* hex = std::getenv(envName);
    if (!hex) {
        return;
    }
    U8 key[64];
    U32 n = 0;
    for (; n < sizeof key && hex[2 * n] && hex[2 * n + 1]; n++) {
        char b[3] = {hex[2 * n], hex[2 * n + 1], 0};
        key[n] = static_cast<U8>(std::strtoul(b, nullptr, 16));
    }
    this->configure(key, n, 0);
}

void CmdAuth::comIn_handler(FwIndexType portNum, Fw::ComBuffer& data, U32 context) {
    if (this->m_keyLen == 0) {
        this->m_rejected++;
        this->log_WARNING_HI_Rejected(CmdAuth_RejectReason::NO_KEY);
        this->tlmWrite_Rejected(this->m_rejected);
        return;
    }
    size_t plen = 0;
    const forge_auth_result_t r =
        this->m_encrypted
            ? forge_auth_open(this->m_kEnc, this->m_kMac, data.getBuffAddr(), data.getBuffLength(), &this->m_last, &plen)
            : forge_auth_verify(this->m_key, this->m_keyLen, data.getBuffAddr(), data.getBuffLength(), &this->m_last, &plen);
    if (r != FORGE_AUTH_OK) {
        this->m_rejected++;
        this->log_WARNING_HI_Rejected(r == FORGE_AUTH_SHORT    ? CmdAuth_RejectReason::TOO_SHORT
                                      : r == FORGE_AUTH_REPLAY ? CmdAuth_RejectReason::REPLAY
                                                               : CmdAuth_RejectReason::BAD_SIGNATURE);
        this->tlmWrite_Rejected(this->m_rejected);
        return;
    }
    Fw::ComBuffer verified(data.getBuffAddr(), static_cast<NATIVE_UINT_TYPE>(plen));
    this->m_accepted++;
    this->tlmWrite_Accepted(this->m_accepted);
    this->tlmWrite_LastCounter(this->m_last);
    this->comOut_out(0, verified, context);
}

void CmdAuth::cmdResponseIn_handler(FwIndexType portNum, FwOpcodeType opCode, U32 cmdSeq,
                                    const Fw::CmdResponse& response) {
    if (this->isConnected_cmdResponseOut_OutputPort(0)) {
        this->cmdResponseOut_out(0, opCode, cmdSeq, response);
    }
}

}  // namespace ForgeSat
