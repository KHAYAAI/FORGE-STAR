// ======================================================================
// \title  StoreForward.cpp
// \brief  FORGE STAR store-and-forward payload component
// ======================================================================
#include "Components/StoreForward/StoreForward.hpp"
#include "FpConfig.hpp"
#include <cstring>

namespace ForgeSat {

StoreForward::StoreForward(const char* const compName)
    : StoreForwardComponentBase(compName), m_passActive(false), m_blocksSent(0), m_passBlocks(0), m_passRecords(0) {
    forge_sf_init(&this->m_store, 0);
}

StoreForward::~StoreForward() {}

void StoreForward::configure(U16 satId) {
    forge_sf_init(&this->m_store, satId);
}

void StoreForward::deviceIn_handler(FwIndexType portNum, U32 shortId, U32 tCreated, I32 latE5, I32 lonE5,
                                    const Fw::StringBase& payload) {
    forge_record_t rec;
    std::memset(&rec, 0, sizeof rec);
    rec.short_id = shortId;
    rec.t_created = tCreated;
    rec.lat_e5 = latE5;
    rec.lon_e5 = lonE5;
    FwSizeType len = payload.length();
    if (len > FORGE_PAYLOAD_MAX) {
        len = FORGE_PAYLOAD_MAX;
    }
    rec.payload_len = static_cast<uint16_t>(len);
    std::memcpy(rec.payload, payload.toChar(), len);
    if (!forge_sf_store(&this->m_store, &rec)) {
        this->log_WARNING_HI_BufferFull();
    }
    this->writeTelemetry();
}

void StoreForward::schedIn_handler(FwIndexType portNum, U32 context) {
    if (!this->m_passActive || !this->isConnected_linkOut_OutputPort(0)) {
        return;
    }
    U32 sent = 0;
    const U32 now = this->getTime().getSeconds();
    const size_t n = forge_sf_next_link_block(&this->m_store, now, this->m_link, sizeof this->m_link, &sent);
    if (n == 0) {
        return;  // nothing left on board this pass
    }
    Fw::Buffer buf(this->m_link, static_cast<U32>(n));
    this->linkOut_out(0, buf);
    this->m_blocksSent++;
    this->m_passBlocks++;
    this->m_passRecords += sent;
    this->writeTelemetry();
}

void StoreForward::SF_PASS_START_cmdHandler(FwOpcodeType opCode, U32 cmdSeq) {
    this->m_passActive = true;
    this->m_passBlocks = 0;
    this->m_passRecords = 0;
    this->log_ACTIVITY_HI_PassStarted(this->m_store.count);
    this->cmdResponse_out(opCode, cmdSeq, Fw::CmdResponse::OK);
}

void StoreForward::SF_PASS_END_cmdHandler(FwOpcodeType opCode, U32 cmdSeq) {
    if (this->m_passActive) {
        this->log_ACTIVITY_HI_PassEnded(this->m_passBlocks, this->m_passRecords);
    }
    this->m_passActive = false;
    this->log_WARNING_HI_BufferFull_ThrottleClear();
    this->cmdResponse_out(opCode, cmdSeq, Fw::CmdResponse::OK);
}

void StoreForward::SF_CLEAR_cmdHandler(FwOpcodeType opCode, U32 cmdSeq) {
    const U32 discarded = this->m_store.count;
    const U16 sat = this->m_store.sat_id;
    const uint32_t seq = this->m_store.seq;
    forge_sf_init(&this->m_store, sat);
    this->m_store.seq = seq;  // sequence numbers keep increasing so the ground never sees a repeat
    this->log_ACTIVITY_HI_Cleared(discarded);
    this->writeTelemetry();
    this->cmdResponse_out(opCode, cmdSeq, Fw::CmdResponse::OK);
}

void StoreForward::writeTelemetry() {
    this->tlmWrite_Stored(this->m_store.count);
    this->tlmWrite_Dropped(this->m_store.dropped);
    this->tlmWrite_BlocksSent(this->m_blocksSent);
}

}  // namespace ForgeSat
