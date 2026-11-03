#ifndef ForgeSat_ModeManager_HPP
#define ForgeSat_ModeManager_HPP

#include "Components/ModeManager/ModeManagerComponentAc.hpp"

namespace ForgeSat {

class ModeManager : public ModeManagerComponentBase {
  public:
    static constexpr F32 SAFE_BELOW_V = 6.6f;     //!< 2S Li-ion: enter safe below this
    static constexpr F32 NOMINAL_ABOVE_V = 7.0f;  //!< allow NOMINAL only above this
    static constexpr U32 POWER_TIMEOUT_TICKS = 30; //!< no bus report for this long -> safe

    explicit ModeManager(const char* const compName);
    ~ModeManager();

  PRIVATE:
    void schedIn_handler(FwIndexType portNum, U32 context) override;
    void busPowerIn_handler(FwIndexType portNum, F32 volts) override;
    void MM_SAFE_cmdHandler(FwOpcodeType opCode, U32 cmdSeq) override;
    void MM_NOMINAL_cmdHandler(FwOpcodeType opCode, U32 cmdSeq) override;
    void enterSafe(const char* reason);

    bool m_safe;
    F32 m_volts;
    U32 m_sinceReport;
};

}  // namespace ForgeSat
#endif
