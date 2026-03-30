(let ((quicklisp-init (merge-pathnames "quicklisp/setup.lisp" (user-homedir-pathname))))
  (when (probe-file quicklisp-init) (load quicklisp-init)))

(format t "~%LOADING OPTICL...~%")
(ql:quickload :opticl)

(defpackage :opencaine-gen (:use :cl :opticl))
(in-package :opencaine-gen)

(defun caine-mutate ()
  (let* ((files (directory "INPUT/*.png"))
         (count (length files)))
    (when (>= count 1)
      (let* ((base (opticl:coerce-image (opticl:read-image-file (first files)) 'opticl:8-bit-rgb-image))
             (out (opticl:copy-image base)))
        (when (> count 1)
          (loop for f in (rest files) do
            (let ((layer (opticl:coerce-image (opticl:read-image-file f) 'opticl:8-bit-rgb-image)))
              (loop for y from 0 below 128 do
                (loop for x from 0 below 128 do
                  (multiple-value-bind (r g b) (opticl:pixel layer y x)
                    (when (> (+ r g b) 200)
                      (multiple-value-bind (or og ob) (opticl:pixel out y x)
                        (setf (opticl:pixel out y x) 
                              (values (floor (/ (+ or r) 2)) 
                                      (floor (/ (+ og g) 2)) 
                                      (floor (/ (+ ob b) 2))))))))))))
        (opticl:write-image-file "output.png" out)))))

(format t "~%ENGINE ONLINE. AWAITING SIGNAL...~%")
(loop
  (if (probe-file "SIGNAL.txt")
      (progn
        (format t "SIGNAL RECEIVED. SYNTHESIZING...~%")
        (caine-mutate)
        (delete-file "SIGNAL.txt")
        (format t "DONE. SLEEPING...~%"))
      (sleep 0.1)))
