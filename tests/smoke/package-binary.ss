(import :clan/base)

(export main)

(def (main . args)
  (display "gerbil-package-executable-ok")
  (for-each
   (lambda (arg)
     (display " ")
     (display arg))
   args)
  (newline))
