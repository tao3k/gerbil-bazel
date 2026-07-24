;;; Native gerbil.pkg evaluator for repository-phase Bazel lowering.
;;;
;;; The manifest is data and is read with Gerbil's own reader.  build.ss is
;;; never parsed here; it is only required as an opaque upstream builder inside
;;; the hermetic source closure.

(import
 :gerbil/gambit
 :std/crypto/digest
 :std/format
 :std/misc/plist
 :std/sort
 :std/srfi/13
 :std/text/hex
 :std/text/json)

(def +schema+ "gerbil-bazel.package-manifest.v1")
(def +manifest-name+ "gerbil.pkg")
(def +builder-name+ "build.ss")
(def +recognized-keys+ '("build" "depend" "package"))
(def +ignored-directories+
  '(".agents"
    ".cache"
    ".codex"
    ".data"
    ".devenv"
    ".direnv"
    ".git"
    ".hg"
    ".idea"
    ".jj"
    ".run"
    ".svn"
    ".vscode"
    "__pycache__"
    "bazel-bin"
    "bazel-out"
    "bazel-testlogs"
    "node_modules"
    "target"))
(def +reserved-files+
  '("BUILD" "BUILD.bazel" "MODULE.bazel" "MODULE.bazel.lock" "WORKSPACE" "WORKSPACE.bazel"))

(def (canonical-json value)
  (parameterize ((write-json-sort-keys? #t))
    (json-object->string value)))

(def (non-empty-string? value)
  (and (string? value) (> (string-length value) 0)))

(def (manifest-atom->string value description)
  (let (text
        (cond
         ((string? value) value)
         ((symbol? value) (symbol->string value))
         (else #f)))
    (unless (non-empty-string? text)
      (error (string-append description " must be a nonempty string or symbol") value))
    text))

(def (read-manifest path)
  (call-with-input-file
   path
   (lambda (port)
     (let ((manifest (read port))
           (trailing (read port)))
       (when (eof-object? manifest)
         (error "gerbil.pkg is empty" path))
       (unless (eof-object? trailing)
         (error "gerbil.pkg must contain exactly one datum" path))
       manifest))))

(def (plist-entries manifest)
  (unless (list? manifest)
    (error "gerbil.pkg must contain a property list" manifest))
  (let loop ((rest manifest) (entries '()))
    (cond
     ((null? rest) (reverse entries))
     ((or (not (pair? rest)) (not (pair? (cdr rest))))
      (error "gerbil.pkg property list has an unmatched key" manifest))
     (else
      (let ((key (car rest))
            (value (cadr rest)))
        (unless (keyword? key)
          (error "gerbil.pkg property keys must be keywords" key))
        (loop
         (cddr rest)
         (cons (cons (keyword->string key) value) entries)))))))

(def (recognized-value entries name fallback)
  (let (matches
        (filter (lambda (entry) (string=? (car entry) name)) entries))
    (when (> (length matches) 1)
      (error "gerbil.pkg contains a duplicate recognized key" name))
    (if (null? matches) fallback (cdar matches))))

(def (dependency-json dependency)
  (let* ((raw (manifest-atom->string dependency "dependency"))
         (parts (string-split raw #\@))
         (package (car parts))
         (tag (and (pair? (cdr parts)) (cadr parts))))
    (unless (non-empty-string? package)
      (error "dependency package identity must be nonempty" raw))
    (hash
     ("package" package)
     ("raw" raw)
     ("tag" (if (non-empty-string? tag) tag (void))))))

(def (canonical-extensions entries)
  (sort
   (map
    (lambda (entry)
      (hash
       ("datum" (format "~s" (cdr entry)))
       ("key" (car entry))))
    (filter
     (lambda (entry) (not (member (car entry) +recognized-keys+)))
     entries))
   (lambda (left right)
     (let ((left-key (hash-ref left "key"))
           (right-key (hash-ref right "key"))
           (left-datum (hash-ref left "datum"))
           (right-datum (hash-ref right "datum")))
       (or
        (string<? left-key right-key)
        (and
         (string=? left-key right-key)
         (string<? left-datum right-datum)))))))

(def (file-sha256 path)
  (call-with-input-file
   path
   (lambda (port)
     (hex-encode (sha256 port)))))

(def (relative-child parent name)
  (if (string=? parent "") name (string-append parent "/" name)))

(def (source-entry root relative)
  (let (path (path-expand relative root))
    (hash
     ("sha256" (file-sha256 path))
     ("path" relative))))

(def (collect-source-entries root)
  (let walk ((relative "") (entries '()))
    (let* ((directory (if (string=? relative "") root (path-expand relative root)))
           (names (sort (directory-files directory) string<?)))
      (let loop ((rest names) (result entries))
        (if (null? rest)
            result
            (let* ((name (car rest))
                   (child-relative (relative-child relative name))
                   (child (path-expand child-relative root))
                   (info (file-info child #f))
                   (type (file-info-type info)))
              (cond
               ((eq? type 'symbolic-link)
                (if (or
                     (member name +ignored-directories+)
                     (and
                      (string=? relative "")
                      (string-prefix? "bazel-" name)))
                    (loop (cdr rest) result)
                    (error "package source closure contains a symbolic link" child-relative)))
               ((eq? type 'directory)
                (if (or
                     (member name +ignored-directories+)
                     (and
                      (string=? relative "")
                      (string-prefix? "bazel-" name)))
                    (loop (cdr rest) result)
                    (loop (cdr rest) (walk child-relative result))))
               ((eq? type 'regular)
                (if (member name +reserved-files+)
                    (loop (cdr rest) result)
                    (loop
                     (cdr rest)
                     (cons (source-entry root child-relative) result))))
               (else
                (error "package source closure contains an unsupported file type"
                       child-relative
                       type)))))))))

(def (closure-sha256 entries)
  (hex-encode
   (sha256
    (string-join
     (map
      (lambda (entry)
        (string-append
         (hash-ref entry "path")
         "\x00;"
         (hash-ref entry "sha256")))
      entries)
     "\n"))))

(def (evaluate-manifest manifest-path)
  (let* ((absolute-manifest (path-normalize (path-expand manifest-path)))
         (root (path-directory absolute-manifest)))
    (unless (string=? (path-strip-directory absolute-manifest) +manifest-name+)
      (error "package manifest must be named gerbil.pkg" manifest-path))
    (unless (eq? (file-info-type (file-info absolute-manifest #f)) 'regular)
      (error "gerbil.pkg must be a regular file" manifest-path))
    (let* ((builder-path (path-expand +builder-name+ root))
           (_
            (unless (and
                     (file-exists? builder-path)
                     (eq? (file-info-type (file-info builder-path #f)) 'regular))
              (error "package root is missing regular build.ss" root)))
           (manifest (read-manifest absolute-manifest))
           (entries (plist-entries manifest))
           (package
            (manifest-atom->string
             (recognized-value entries "package" #f)
             "package identity"))
           (dependencies-value
            (recognized-value entries "depend" '()))
           (_
            (unless (list? dependencies-value)
              (error "gerbil.pkg depend: must be a list" dependencies-value)))
           (_ (recognized-value entries "build" #f))
           (sources
            (sort
             (collect-source-entries root)
             (lambda (left right)
               (string<? (hash-ref left "path") (hash-ref right "path"))))))
      (hash
       ("closureSha256" (closure-sha256 sources))
       ("dependencies" (map dependency-json dependencies-value))
       ("evaluator"
        (hash
         ("gambitVersion" (system-version-string))
         ("gerbilVersion" (gerbil-version-string))))
       ("extensions" (canonical-extensions entries))
       ("manifest" +manifest-name+)
       ("package" package)
       ("schema" +schema+)
       ("sources" sources)))))

(def (main manifest-path)
  (displayln (canonical-json (evaluate-manifest manifest-path))))
