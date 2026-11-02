// ======================================================================
// \title  StoreForwardTester.hpp
// \brief  Unit-test harness for the StoreForward component
// ======================================================================
#ifndef ForgeSat_StoreForwardTester_HPP
#define ForgeSat_StoreForwardTester_HPP

#include <vector>
#include "Components/StoreForward/StoreForward.hpp"
#include "Components/StoreForward/StoreForwardGTestBase.hpp"

namespace ForgeSat {

class StoreForwardTester : public StoreForwardGTestBase {
  public:
    static const FwSizeType MAX_HISTORY_SIZE = 4000;
    static const FwEnumStoreType TEST_INSTANCE_ID = 0;
    static const FwSizeType TEST_INSTANCE_QUEUE_DEPTH = 10;

    StoreForwardTester();
    ~StoreForwardTester();

    void testStoreAndDownlinkPass();   //!< messages stored, pass drains them as valid link blocks
    void testNoDownlinkOutsidePass();  //!< ticks outside a pass send nothing
    void testBufferFullDropsAndWarns();
    void testClearKeepsSequenceMoving();
    void testPassPredictorInput();   //!< passIn port starts and ends passes like the commands

  private:
    void from_linkOut_handler(FwIndexType portNum, Fw::Buffer& fwBuffer) override;
    void sendDevice(U32 i);
    void tick(U32 n);
    void connectPorts();
    void initComponents();

    StoreForward component;
    std::vector<std::vector<U8>> m_blocks;  //!< copies of every link block sent
};

}  // namespace ForgeSat
#endif
