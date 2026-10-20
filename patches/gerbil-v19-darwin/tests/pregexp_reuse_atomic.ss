(import :std/text/pregexp :std/encoding/json :gerbil-mcp/util/strings)

(def patterns
  '("/home/|/usr/|/opt/|/tmp/|/var/"
    "^[a-zA-Z][a-zA-Z0-9_-]*/[a-zA-Z]"
    "^[a-zA-Z][a-zA-Z0-9_-]*/[a-zA-Z][a-zA-Z0-9_/-]*$"
    "v[0-9]+\\.[0-9]+\\.[0-9]+.*gambit|Gambit"
    "gerbil|Gerbil"
    "--prefix=|--enable-|--disable-|--with-|configure\\s"
    "gcc|g\\+\\+|clang"
    "[0-9]+\\.[0-9]+"
    "[a-z]+-[a-z]+[?!]$"
    "^make-[a-z]"))

(def strings
  (call-with-input-file (getenv "PREGEXP_ATOMIC_STRINGS")
    (lambda (port)
      (let loop ((remaining 2000) (out '()))
        (if (= remaining 0) (reverse out)
          (let (line (read-line port))
            (if (eof-object? line) (reverse out)
              (loop (- remaining 1) (cons (str-trim line) out)))))))))

(def compiled (map pregexp patterns))
(def (matches pats)
  (map (lambda (s) (map (lambda (p) (pregexp-match-positions p s)) pats)) strings))
(def reference #f)
(for-each
 (lambda (mode)
   (let* ((started (real-time))
          (result (matches (if (equal? mode "literal") patterns compiled)))
          (seconds (- (real-time) started)))
     (if reference
       (unless (equal? result reference) (error "pattern reuse changed match positions"))
       (set! reference result))
     (displayln (json->string
                  (hash ("mode" mode) ("seconds" seconds)
                        ("strings" (length strings)) ("patterns" (length patterns))
                        ("exactPositionsMatch" #t))))
     (force-output)))
 '("literal" "compiled" "compiled" "literal"))
(displayln "OK")
