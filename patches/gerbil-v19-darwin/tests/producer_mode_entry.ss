(export main)
(extern namespace: #f mode-value)
(begin-foreign
  (c-declare "#ifdef ___DYNAMIC\nint producer_mode_value(void) { return 17; }\n#else\nint producer_mode_value(void) { return 29; }\n#endif")
  (define mode-value (c-lambda () int "producer_mode_value")))

(def (main . args)
  (displayln "PRODUCER-MODE=" (mode-value)))
