// ======================================================================
// \title  StoreForward.cpp
// \brief  FORGE STAR store-and-forward payload component
// ======================================================================
#include "Components/StoreForward/StoreForward.hpp"
#include "FpConfig.hpp"
#include <cstdio>
#include <cstring>

namespace ForgeSat {

StoreForward::StoreForward(const char* const compName)
    : StoreForwardComponentBase(compName), m_passActive(false), m_blocksSent(0), m_passBlocks(0), m_passRecords(0), m_ackedOnBoard(0),
      m_safe(false), m_saveEvery(0), m_ticks(0) {
    forge_sf_init(&this->m_store, 0);
    this->m_path[0] = 0;
}

StoreForward::~StoreForward() {}

void StoreForward::configure(U16 satId) {
    forge_sf_init(&this->m_store, satId);
}

void StoreForward::configurePersistence(const char* path, U32 saveEvery) {
    std::snprintf(this->m_path, sizeof this->m_path, "%s", path);
    this->m_saveEvery = saveEvery;
    // Restore what was on board before a reboot. A missing or damaged image just means an empty store.
    if (FILE* f = std::fopen(this->m_path, "rb")) {
        const size_t n = std::fread(this->m_img, 1, sizeof this->m_img, f);
        std::fclose(f);
        forge_sf_t tmp;
        const U16 sat = this->m_store.sat_id;
        if (forge_sf_load(&tmp, this->m_img, n) && tmp.sat_id == sat) {
            this->m_store = tmp;
            this->log_ACTIVITY_HI_Restored(this->m_store.count);
        }
    }
}

void StoreForward::save() {
    if (!this->m_path[0]) {
        return;
    }
    const size_t n = forge_sf_save(&this->m_store, this->m_img, sizeof this->m_img);
    char tmp[140];
    std::snprintf(tmp, sizeof tmp, "%s.tmp", this->m_path);
    if (FILE* f = std::fopen(tmp, "wb")) {       // write-then-rename so a reset mid-write never corrupts the image
        const bool ok = std::fwrite(this->m_img, 1, n, f) == n;
        std::fclose(f);
        if (ok && std::rename(tmp, this->m_path) == 0) {
            this->log_ACTIVITY_LO_Saved(this->m_store.count, static_cast<U32>(n));
        }
    }
}

void StoreForward::modeIn_handler(FwIndexType portNum, bool safe) {
    if (safe == this->m_safe) {
        return;
    }
    this->m_safe = safe;
    if (safe) {
        this->endPass();       // stop transmitting immediately
        this->save();          // a safe-mode entry may precede a reset: keep the store
    }
    this->log_ACTIVITY_HI_ModeChanged(safe);
    this->writeTelemetry();
}

void StoreForward::SF_SAVE_cmdHandler(FwOpcodeType opCode, U32 cmdSeq) {
    this->save();
    this->cmdResponse_out(opCode, cmdSeq, this->m_path[0] ? Fw::CmdResponse::OK : Fw::CmdResponse::EXECUTION_ERROR);
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
    this->m_ticks++;
    if (this->m_ticks % 10 == 0) {                    // memory scrubbing
        const U32 bad = forge_sf_scrub(&this->m_store);
        if (bad) {
            this->log_WARNING_LO_Scrubbed(bad);
        }
    }
    if (this->m_saveEvery && this->m_ticks % this->m_saveEvery == 0) {
        this->save();
    }
    if (this->m_safe || !this->m_passActive || !this->isConnected_linkOut_OutputPort(0)) {
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

void StoreForward::startPass() {
    if (this->m_passActive || this->m_safe) {
        return;               // no transmission in safe mode
    }
    this->m_passActive = true;
    this->m_passBlocks = 0;
    this->m_passRecords = 0;
    this->log_ACTIVITY_HI_PassStarted(this->m_store.count);
}

void StoreForward::endPass() {
    if (this->m_passActive) {
        this->log_ACTIVITY_HI_PassEnded(this->m_passBlocks, this->m_passRecords);
        this->m_passActive = false;
        this->save();
    }
    this->m_passActive = false;
    this->log_WARNING_HI_BufferFull_ThrottleClear();
}

void StoreForward::passIn_handler(FwIndexType portNum, bool inView) {
    if (inView) {
        this->startPass();
    } else {
        this->endPass();
    }
}

void StoreForward::ackIn_handler(FwIndexType portNum, Fw::Buffer& fwBuffer) {
    U16 gw = 0;
    const int n = forge_ack_decode(fwBuffer.getData(), fwBuffer.getSize(), this->m_ackKeys,
                                   FW_NUM_ARRAY_ELEMENTS(this->m_ackKeys), &gw);
    if (n < 0) {
        this->log_WARNING_LO_BadAck();
    } else {
        const U32 removed = forge_sf_apply_acks(&this->m_store, this->m_ackKeys, static_cast<size_t>(n));
        this->m_ackedOnBoard += removed;
        this->log_ACTIVITY_LO_AcksApplied(static_cast<U32>(n), removed);
        this->writeTelemetry();
    }
    if (this->isConnected_ackReturn_OutputPort(0)) {
        this->ackReturn_out(0, fwBuffer);
    }
}

void StoreForward::SF_PASS_START_cmdHandler(FwOpcodeType opCode, U32 cmdSeq) {
    this->startPass();
    this->cmdResponse_out(opCode, cmdSeq, Fw::CmdResponse::OK);
}

void StoreForward::SF_PASS_END_cmdHandler(FwOpcodeType opCode, U32 cmdSeq) {
    this->endPass();
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
    this->tlmWrite_AckedOnBoard(this->m_ackedOnBoard);
    this->tlmWrite_Corrupted(this->m_store.corrupted);
    this->tlmWrite_SafeMode(this->m_safe);
}

}  // namespace ForgeSat
