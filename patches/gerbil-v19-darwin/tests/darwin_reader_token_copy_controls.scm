(load (getenv "READER_WHITESPACE_CONTROLS"))
(let* ((rt (##readtable-copy (current-readtable)))
       (port (open-input-string "foo\nbar\nbaz ")))
  (##readtable-char-delimiter?-set! rt #\newline #f)
  (peek-char port)
  (parameterize ((current-readtable rt))
    (check "fused copy retains Unicode prefix and multiple newlines"
      (equal? (##gb-darwin-buffered-token (get-readenv port) unicode 3)
              (string-append (make-string 3 unicode) "foo\nbar\nbaz"))))
  (check "fused copy commits exact multi-line position"
    (and (= (input-port-line port) 3) (= (input-port-column port) 4)))
  (check "fused copy leaves final delimiter unconsumed"
    (char=? (peek-char port) #\space)))
(display "OK") (newline) (force-output)
