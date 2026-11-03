// ======================================================================
// \title  StoreForwardTestMain.cpp
// \brief  Test entry point for StoreForward
// ======================================================================
#include <memory>
#include "StoreForwardTester.hpp"  // testers live on the heap: the component holds a multi-MB store

TEST(Nominal, StoreAndDownlinkPass) { std::unique_ptr<ForgeSat::StoreForwardTester> t(new ForgeSat::StoreForwardTester()); t->testStoreAndDownlinkPass(); }
TEST(Nominal, NoDownlinkOutsidePass) { std::unique_ptr<ForgeSat::StoreForwardTester> t(new ForgeSat::StoreForwardTester()); t->testNoDownlinkOutsidePass(); }
TEST(OffNominal, BufferFullDropsAndWarns) { std::unique_ptr<ForgeSat::StoreForwardTester> t(new ForgeSat::StoreForwardTester()); t->testBufferFullDropsAndWarns(); }
TEST(OffNominal, ClearKeepsSequenceMoving) { std::unique_ptr<ForgeSat::StoreForwardTester> t(new ForgeSat::StoreForwardTester()); t->testClearKeepsSequenceMoving(); }

TEST(Nominal, PassPredictorInput) { std::unique_ptr<ForgeSat::StoreForwardTester> t(new ForgeSat::StoreForwardTester()); t->testPassPredictorInput(); }

TEST(Nominal, AcksDropStoredDuplicates) { std::unique_ptr<ForgeSat::StoreForwardTester> t(new ForgeSat::StoreForwardTester()); t->testAcksDropStoredDuplicates(); }

int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
