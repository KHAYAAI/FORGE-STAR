// ======================================================================
// \title  CmdAuth.hpp
// \brief  HMAC-SHA256 command authentication with replay protection
// ======================================================================
#ifndef ForgeSat_CmdAuth_HPP
#define ForgeSat_CmdAuth_HPP

#include "Components/CmdAuth/CmdAuthComponentAc.hpp"

namespace ForgeSat {

class CmdAuth : public CmdAuthComponentBase {
  public:
    explicit CmdAuth(const char* const compName);
    ~CmdAuth();

    //! Load the per-satellite key. On the satellite this comes from protected storage;
    //! on the ground test builds from FORGE_CMD_KEY (hex). Without a key every command is rejected.
    void configure(const U8* key, U32 len, U32 lastCounter);
    void configureFromHexEnv(const char* envName);

  PRIVATE:
    void comIn_handler(FwIndexType portNum, Fw::ComBuffer& data, U32 context) override;
    void cmdResponseIn_handler(FwIndexType portNum, FwOpcodeType opCode, U32 cmdSeq,
                               const Fw::CmdResponse& response) override;

    U8 m_key[64];
    U32 m_keyLen;
    U32 m_last;
    U32 m_accepted;
    U32 m_rejected;
};

}  // namespace ForgeSat
#endif
