(import :gerbil-mcp/util/cookbook :gerbil-mcp/util/verify
        (only-in :gerbil-mcp/mcp/toolkit take*) :std/encoding/json)

(def recipes (load-recipes))
(def indices '(0 1 2))
(def rows
  (map
   (lambda (index)
     (let* ((tail (list-tail recipes (* index +default-batch-size+)))
            (batch (take* tail +default-batch-size+)))
       (let-values (((imports checks) (build-verify-expressions batch)))
         (hash ("index" index) ("ids" (map recipe-id batch))
               ("imports" imports) ("checks" checks)))))
   indices))
(displayln (json->string
            (hash ("recipeCount" (length recipes))
                  ("batchSize" +default-batch-size+) ("batches" rows))))
