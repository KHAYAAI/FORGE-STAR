// ======================================================================
// \title  StoreForwardTester.cpp
// \brief  Unit tests for the StoreForward component
// ======================================================================
#include "StoreForwardTester.hpp"
#include <cstdio>
#include <cstring>

namespace ForgeSat {

StoreForwardTester::StoreForwardTester()
    : StoreForwardGTestBase("StoreForwardTester", StoreForwardTester::MAX_HISTORY_SIZE), component("StoreForward") {
    this->initComponents();
    this->connectPorts();
    this->component.configure(7);
    Fw::Time t(TB_NONE, 1790009999u, 0);
    this->setTestTime(t);  // the component stamps downlink time from this
}

StoreForwardTester::~StoreForwardTester() {}

void StoreForwardTester::from_linkOut_handler(FwIndexType portNum, Fw::Buffer& fwBuffer) {
    // The component lends its buffer only for the duration of the call: copy it.
    this->m_blocks.emplace_back(fwBuffer.getData(), fwBuffer.getData() + fwBuffer.getSize());
    this->pushFromPortEntry_linkOut(fwBuffer);
}

void StoreForwardTester::sendDevice(U32 i) {
    char json[64];
    std::snprintf(json, sizeof json, "{\"flow_lpm\":%u}", static_cast<unsigned>(i));
    Fw::String payload(json);
    this->invoke_to_deviceIn(0, 0x1234u + i, 1790000000u + i, -2412345, 2954321, payload);
    this->component.doDispatch();
}

void StoreForwardTester::tick(U32 n) {
    for (U32 i = 0; i < n; i++) {
        this->invoke_to_schedIn(0, 0);
        this->component.doDispatch();
    }
}

void StoreForwardTester::testStoreAndDownlinkPass() {
    for (U32 i = 0; i < 150; i++) {
        this->sendDevice(i);
    }
    ASSERT_TLM_Stored_SIZE(150);
    ASSERT_TLM_Stored(149, 150);
    this->clearHistory();

    this->sendCmd_SF_PASS_START(0, 1);
    this->component.doDispatch();
    ASSERT_CMD_RESPONSE(0, StoreForward::OPCODE_SF_PASS_START, 1, Fw::CmdResponse::OK);
    ASSERT_EVENTS_PassStarted(0, 150);

    this->tick(20);  // more ticks than needed: extra ticks must send nothing
    ASSERT_GT(this->m_blocks.size(), 1u);
    for (const auto& b : this->m_blocks) {
        ASSERT_GE(b.size(), 4u + 255u);
        ASSERT_EQ(0u, (b.size() - 4u) % 255u);  // whole RS codewords
        ASSERT_EQ(0x1A, b[0]); ASSERT_EQ(0xCF, b[1]); ASSERT_EQ(0xFC, b[2]); ASSERT_EQ(0x1D, b[3]);  // ASM
    }

    this->sendCmd_SF_PASS_END(0, 2);
    this->component.doDispatch();
    ASSERT_EVENTS_PassEnded(0, static_cast<U32>(this->m_blocks.size()), 150);

    // The same inputs through libforge directly must give identical bytes (component adds no framing).
    static forge_sf_t ref;
    forge_sf_init(&ref, 7);
    for (U32 i = 0; i < 150; i++) {
        forge_record_t r;
        std::memset(&r, 0, sizeof r);
        r.short_id = 0x1234u + i; r.t_created = 1790000000u + i; r.lat_e5 = -2412345; r.lon_e5 = 2954321;
        r.payload_len = static_cast<uint16_t>(std::snprintf(reinterpret_cast<char*>(r.payload), FORGE_PAYLOAD_MAX,
                                                            "{\"flow_lpm\":%u}", static_cast<unsigned>(i)));
        forge_sf_store(&ref, &r);
    }
    static U8 buf[FORGE_LINK_MAX];
    U32 sent = 0;
    for (const auto& b : this->m_blocks) {
        const size_t n = forge_sf_next_link_block(&ref, 1790009999u, buf, sizeof buf, &sent);
        ASSERT_EQ(b.size(), n);
        ASSERT_EQ(0, std::memcmp(buf, b.data(), n));
    }

    // Optional: dump for the Python ground decoder (tests/test_flight_c.py style check)
    if (const char* path = std::getenv("FORGE_UT_DUMP")) {
        if (FILE* f = std::fopen(path, "wb")) {
            for (const auto& b : this->m_blocks) std::fwrite(b.data(), 1, b.size(), f);
            std::fclose(f);
        }
    }
}

void StoreForwardTester::testNoDownlinkOutsidePass() {
    for (U32 i = 0; i < 5; i++) this->sendDevice(i);
    this->tick(5);
    ASSERT_from_linkOut_SIZE(0);
}

void StoreForwardTester::testBufferFullDropsAndWarns() {
    for (U32 i = 0; i < FORGE_SF_CAPACITY + 3; i++) this->sendDevice(i);
    ASSERT_EVENTS_BufferFull_SIZE(3);
    ASSERT_TLM_Dropped(FORGE_SF_CAPACITY + 2, 3);
    ASSERT_TLM_Stored(FORGE_SF_CAPACITY + 2, FORGE_SF_CAPACITY);
}

void StoreForwardTester::testClearKeepsSequenceMoving() {
    for (U32 i = 0; i < 3; i++) this->sendDevice(i);
    this->sendCmd_SF_PASS_START(0, 1); this->component.doDispatch();
    this->tick(1);
    ASSERT_EQ(1u, this->m_blocks.size());
    for (U32 i = 0; i < 4; i++) this->sendDevice(i);
    this->clearHistory();
    this->sendCmd_SF_CLEAR(0, 3); this->component.doDispatch();
    ASSERT_EVENTS_Cleared(0, 4);
    ASSERT_TLM_Stored(0, 0);
    this->sendDevice(9); this->tick(1);
    ASSERT_EQ(2u, this->m_blocks.size());
    // frame sequence number sits after the ASM + 3-byte link header, de-randomised
    U8 a[16], b[16];
    std::memcpy(a, this->m_blocks[0].data() + 4, 16); forge_randomise(a, 16);
    std::memcpy(b, this->m_blocks[1].data() + 4, 16); forge_randomise(b, 16);
    const U32 seqA = (U32(a[3 + 4]) << 24) | (U32(a[3 + 5]) << 16) | (U32(a[3 + 6]) << 8) | a[3 + 7];
    const U32 seqB = (U32(b[3 + 4]) << 24) | (U32(b[3 + 5]) << 16) | (U32(b[3 + 6]) << 8) | b[3 + 7];
    ASSERT_EQ(seqA + 1, seqB);
}

void StoreForwardTester::testPassPredictorInput() {
    for (U32 i = 0; i < 10; i++) this->sendDevice(i);
    this->invoke_to_passIn(0, true);
    this->component.doDispatch();
    ASSERT_EVENTS_PassStarted(0, 10);
    this->tick(3);
    ASSERT_EQ(1u, this->m_blocks.size());   // 10 small messages fit one link block
    this->invoke_to_passIn(0, false);
    this->component.doDispatch();
    ASSERT_EVENTS_PassEnded(0, 1, 10);
    for (U32 i = 0; i < 3; i++) this->sendDevice(i);
    this->tick(3);
    ASSERT_EQ(1u, this->m_blocks.size());   // pass over: nothing more sent
}

void StoreForwardTester::testAcksDropStoredDuplicates() {
    for (U32 i = 0; i < 5; i++) this->sendDevice(i);       // short ids 0x1234+i, t 1790000000+i
    // build an ACK frame for messages 1 and 3, exactly as the gateway does (forgestar/frames.py)
    static U8 f[16 + 2 * 8 + 4];
    std::memset(f, 0, sizeof f);
    f[0] = 0xF6; f[1] = 1; f[3] = 4;                       // magic, version, gateway 4
    f[13] = 2;                                             // two entries
    const U32 ids[2] = {0x1234u + 1, 0x1234u + 3}, ts[2] = {1790000001u, 1790000003u};
    for (int k = 0; k < 2; k++) {
        for (int b = 0; b < 4; b++) {
            f[16 + k * 8 + b] = static_cast<U8>(ids[k] >> (24 - 8 * b));
            f[20 + k * 8 + b] = static_cast<U8>(ts[k] >> (24 - 8 * b));
        }
    }
    const U32 crc = forge_crc32(f, sizeof f - 4);
    for (int b = 0; b < 4; b++) f[sizeof f - 4 + b] = static_cast<U8>(crc >> (24 - 8 * b));
    this->clearHistory();
    Fw::Buffer buf(f, sizeof f);
    this->invoke_to_ackIn(0, buf);
    this->component.doDispatch();
    ASSERT_EVENTS_AcksApplied(0, 2, 2);
    ASSERT_from_ackReturn_SIZE(1);                          // buffer handed back to its owner
    ASSERT_TLM_Stored(0, 3);
    ASSERT_TLM_AckedOnBoard(0, 2);
    f[20] ^= 1;                                             // corrupt -> rejected, buffer still returned
    this->invoke_to_ackIn(0, buf);
    this->component.doDispatch();
    ASSERT_EVENTS_BadAck_SIZE(1);
    ASSERT_from_ackReturn_SIZE(2);
}

}  // namespace ForgeSat
