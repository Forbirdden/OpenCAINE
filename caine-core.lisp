(let ((quicklisp-init (merge-pathnames "quicklisp/setup.lisp" (user-homedir-pathname))))
  (when (probe-file quicklisp-init) (load quicklisp-init)))

(format t "~% RELOADING ENGINE...~%")
(ql:quickload '(:opticl :alexandria))

(defpackage :opencaine-gen (:use :cl :opticl))
(in-package :opencaine-gen)

(defun load-config (filename)
  (if (probe-file filename)
      (with-open-file (in filename) (read in))
      (list :epochs 1 :target-ratio 0.35 :learning-rate 45.0 :chaos-level 20)))

(defun clamp (val) (max 0 (min 255 val)))

(defun caine-mutate (config)
  (let* ((files (directory "INPUT/*.png"))
         (count (length files))
         (epochs (getf config :epochs 1))
         (target (getf config :target-ratio 0.35))
         (lr (/ (getf config :learning-rate 45.0) 100.0))
         (chaos (getf config :chaos-level 20)))
    
    (when (>= count 1)
      (let* ((base (opticl:coerce-image (opticl:read-image-file (first files)) 'opticl:8-bit-rgb-image))
             (out (opticl:copy-image base)))
        
        (dotimes (e epochs)
          (when (> count 1)
            (loop for f in (rest files) do
              (let ((layer (opticl:coerce-image (opticl:read-image-file f) 'opticl:8-bit-rgb-image)))
                (opticl:with-image-bounds (h w) layer
                  (loop for y from 0 below h do
                    (loop for x from 0 below w do
                      (multiple-value-bind (r g b) (opticl:pixel layer y x)
                        (when (> (+ r g b chaos) (* 765 target))
                          (multiple-value-bind (or og ob) (opticl:pixel out y x)
                            (setf (opticl:pixel out y x) 
                                  (values (clamp (floor (+ or (* (- r or) lr))))
                                          (clamp (floor (+ og (* (- g og) lr))))
                                          (clamp (floor (+ ob (* (- b ob) lr))))))))))))))))
        (opticl:write-image-file "output.png" out)))))

(format t "~%ENGINE ONLINE. SYSTEM TIME: 30.03.2026. AWAITING SIGNAL...~%")

(loop
  (if (probe-file "SIGNAL.txt")
      (let ((config (load-config "paraphernalia-engine.dat")))
        (format t "SIGNAL RECEIVED. CONFIG: ~A~%" config)
        (caine-mutate config)
        (delete-file "SIGNAL.txt")
        (format t "SYNTHESIS COMPLETE.~%"))
      (sleep 0.1)))
