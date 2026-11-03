#ifndef ForgeSat_PassPredictor_HPP
#define ForgeSat_PassPredictor_HPP

#include "Components/PassPredictor/PassPredictorComponentAc.hpp"
#include "forge_orbit.h"

namespace ForgeSat {

class PassPredictor : public PassPredictorComponentBase {
  public:
    static constexpr U32 MAX_GATEWAYS = 8;
    explicit PassPredictor(const char* const compName);
    ~PassPredictor();

    //! simSecondsPerTick > 0 runs on a simulated clock (ground tests); 0 = spacecraft time
    void configure(F64 simSecondsPerTick);
    void setElements(const forge_elements_t& el);
    void setGateway(U32 slot, F64 latDeg, F64 lonDeg, F64 maskDeg);

  PRIVATE:
    void schedIn_handler(FwIndexType portNum, U32 context) override;
    void PP_SET_ELEMENTS_cmdHandler(FwOpcodeType opCode, U32 cmdSeq, U32 epoch, F32 altKm, F32 incDeg, F32 raanDeg,
                                    F32 uDeg, F32 gmstDeg) override;
    void PP_SET_GATEWAY_cmdHandler(FwOpcodeType opCode, U32 cmdSeq, U8 slot, F32 latDeg, F32 lonDeg, F32 maskDeg) override;
    F64 now();
    U32 activeGateways(forge_gateway_t* out);

    forge_elements_t m_el;
    bool m_haveEl;
    forge_gateway_t m_gw[MAX_GATEWAYS];
    bool m_gwOn[MAX_GATEWAYS];
    bool m_inView;
    F64 m_simDt, m_simT;
    U32 m_ticks;
};

}  // namespace ForgeSat
#endif
