(c-declare "#include <mach-o/dyld.h>")
(define bundle-image-count (c-lambda () unsigned-int "_dyld_image_count"))
