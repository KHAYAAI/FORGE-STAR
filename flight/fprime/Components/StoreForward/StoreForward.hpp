// ======================================================================
// \title  StoreForward.hpp
// \brief  FORGE STAR store-and-forward payload component (wraps flight/libforge)
// ======================================================================
#ifndef ForgeSat_StoreForward_HPP
#define ForgeSat_StoreForward_HPP

#include "Components/StoreForward/StoreForwardComponentAc.hpp"
#include "forge.h"

namespace ForgeSat {

class StoreForward : public StoreForwardComponentBase {
  public:
    explicit StoreForward(const char* const compName);
    ~StoreForward();

    //! Set the satellite id written into every downlink frame (call before start)
    void configure(U16 satId);

    //! Persistent storage for the onboard store: loaded now, saved after each pass, every saveEvery ticks and on SF_SAVE
    void configurePersistence(const char* path, U32 saveEvery);

  PRIVATE:
    void deviceIn_handler(FwIndexType portNum, U32 shortId, U32 tCreated, I32 latE5, I32 lonE5,
                          const Fw::StringBase& payload) override;
    void schedIn_handler(FwIndexType portNum, U32 context) override;
    void passIn_handler(FwIndexType portNum, bool inView) override;
    void ackIn_handler(FwIndexType portNum, Fw::Buffer& fwBuffer) override;
    void modeIn_handler(FwIndexType portNum, bool safe) override;
    void SF_SAVE_cmdHandler(FwOpcodeType opCode, U32 cmdSeq) override;
    void save();
    void startPass();
    void endPass();
    void SF_PASS_START_cmdHandler(FwOpcodeType opCode, U32 cmdSeq) override;
    void SF_PASS_END_cmdHandler(FwOpcodeType opCode, U32 cmdSeq) override;
    void SF_CLEAR_cmdHandler(FwOpcodeType opCode, U32 cmdSeq) override;

    void writeTelemetry();

    forge_sf_t m_store;                       //!< onboard ring buffer (libforge)
    U8 m_link[FORGE_LINK_MAX];                //!< one link block, lent to linkOut during the call
    bool m_passActive;
    U32 m_blocksSent;                         //!< since boot
    U32 m_passBlocks;
    U32 m_passRecords;
    U32 m_ackedOnBoard;                       //!< since boot
    forge_ack_key_t m_ackKeys[512];
    bool m_safe;
    char m_path[128];
    U32 m_saveEvery;
    U32 m_ticks;
    U8 m_img[FORGE_SF_CAPACITY * (FORGE_REC_HDR + FORGE_PAYLOAD_MAX) + 64];
};

}  // namespace ForgeSat
#endif
