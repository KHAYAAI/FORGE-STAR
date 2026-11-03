set(SOURCE_FILES
  "${CMAKE_CURRENT_LIST_DIR}/ModeManager.fpp"
  "${CMAKE_CURRENT_LIST_DIR}/ModeManager.cpp"
)
set(MOD_DEPS Components_StoreForward)
register_fprime_module()
