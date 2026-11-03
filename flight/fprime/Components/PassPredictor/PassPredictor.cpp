#include "Components/PassPredictor/PassPredictor.hpp"
#include "FpConfig.hpp"
#include <cmath>

namespace ForgeSat {

static const F64 DEG = 3.14159265358979323846 / 180.0;

PassPredictor::PassPredictor(const char* const compName)
    : PassPredictorComponentBase(compName), m_haveEl(false), m_inView(false), m_simDt(0.0), m_simT(0.0), m_ticks(0) {
    for (U32 i = 0; i < MAX_GATEWAYS; i++) {
        this->m_gwOn[i] = false;
    }
}

PassPredictor::~PassPredictor() {}

void PassPredictor::configure(F64 simSecondsPerTick) {
    this->m_simDt = simSecondsPerTick;
}

void PassPredictor::setElements(const forge_elements_t& el) {
    this->m_el = el;
    this->m_haveEl = true;
    this->m_simT = el.epoch;
}

void PassPredictor::setGateway(U32 slot, F64 latDeg, F64 lonDeg, F64 maskDeg) {
    if (slot >= MAX_GATEWAYS) {
        return;
    }
    this->m_gw[slot] = {latDeg * DEG, lonDeg * DEG, maskDeg * DEG};
    this->m_gwOn[slot] = maskDeg > 0.0;
}

F64 PassPredictor::now() {
    if (this->m_simDt > 0.0) {
        return this->m_simT;
    }
    const Fw::Time t = this->getTime();
    return static_cast<F64>(t.getSeconds()) + static_cast<F64>(t.getUSeconds()) * 1e-6;
}

U32 PassPredictor::activeGateways(forge_gateway_t* out) {
    U32 n = 0;
    for (U32 i = 0; i < MAX_GATEWAYS; i++) {
        if (this->m_gwOn[i]) {
            out[n++] = this->m_gw[i];
        }
    }
    return n;
}

void PassPredictor::schedIn_handler(FwIndexType portNum, U32 context) {
    if (this->m_simDt > 0.0) {
        this->m_simT += this->m_simDt;
    }
    if (!this->m_haveEl) {
        return;
    }
    forge_gateway_t gws[MAX_GATEWAYS];
    const U32 n = this->activeGateways(gws);
    const F64 t = this->now();
    const bool inView = n > 0 && forge_orbit_gateway_in_view(&this->m_el, t, gws, static_cast<int>(n));
    if (inView != this->m_inView) {
        this->m_inView = inView;
        this->log_ACTIVITY_LO_PassPredicted(inView);
        if (this->isConnected_passOut_OutputPort(0)) {
            this->passOut_out(0, inView);
        }
    }
    if (this->m_ticks++ % 30 == 0) {
        const F64 nxt = n ? forge_orbit_next_pass(&this->m_el, t, gws, static_cast<int>(n), 10.0, 2 * 86400.0) : -1.0;
        this->tlmWrite_NextPassS(static_cast<F32>(nxt));
    }
    this->tlmWrite_InView(inView);
}

void PassPredictor::PP_SET_ELEMENTS_cmdHandler(FwOpcodeType opCode, U32 cmdSeq, U32 epoch, F32 altKm, F32 incDeg,
                                               F32 raanDeg, F32 uDeg, F32 gmstDeg) {
    if (altKm < 150.0f || altKm > 2000.0f) {
        this->cmdResponse_out(opCode, cmdSeq, Fw::CmdResponse::VALIDATION_ERROR);
        return;
    }
    forge_elements_t el = {static_cast<double>(epoch), altKm, incDeg * DEG, raanDeg * DEG, uDeg * DEG, gmstDeg * DEG};
    this->setElements(el);
    this->log_ACTIVITY_HI_ElementsLoaded(epoch, altKm, incDeg);
    this->cmdResponse_out(opCode, cmdSeq, Fw::CmdResponse::OK);
}

void PassPredictor::PP_SET_GATEWAY_cmdHandler(FwOpcodeType opCode, U32 cmdSeq, U8 slot, F32 latDeg, F32 lonDeg,
                                              F32 maskDeg) {
    if (slot >= MAX_GATEWAYS || std::fabs(latDeg) > 90.0f || std::fabs(lonDeg) > 180.0f) {
        this->cmdResponse_out(opCode, cmdSeq, Fw::CmdResponse::VALIDATION_ERROR);
        return;
    }
    this->setGateway(slot, latDeg, lonDeg, maskDeg);
    this->log_ACTIVITY_LO_GatewaySet(slot, latDeg, lonDeg);
    this->cmdResponse_out(opCode, cmdSeq, Fw::CmdResponse::OK);
}

}  // namespace ForgeSat
