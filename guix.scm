;; ScatterBackup - A chaotic backup solution
;; Copyright (C) 2020 Ingo Ruhnke <grumbel@gmail.com>
;;
;; This program is free software: you can redistribute it and/or modify
;; it under the terms of the GNU General Public License as published by
;; the Free Software Foundation, either version 3 of the License, or
;; (at your option) any later version.
;;
;; This program is distributed in the hope that it will be useful,
;; but WITHOUT ANY WARRANTY; without even the implied warranty of
;; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
;; GNU General Public License for more details.
;;
;; You should have received a copy of the GNU General Public License
;; along with this program.  If not, see <http://www.gnu.org/licenses/>.

(set! %load-path
  (cons* "/ipfs/QmTvbrDG1ef73qbgQ5LN3RA1bHPFHQmmEdHRuuSL7ntsr8/guix-cocfree_0.0.0-59-gd79b2bf"
         %load-path))

(use-modules (guix packages)
             (guix build-system python)
             ((guix licenses) #:prefix license:)
             (gnu packages freedesktop)
             (gnu packages python)
             (gnu packages python-xyz)
             (guix-cocfree packages python-bytefmt)
             (guix-cocfree utils))

(define %source-dir (dirname (current-filename)))

(define-public scatterbackup
  (package
   (name "scatterbackup")
   (version (version-from-source %source-dir))
   (source (source-from-source %source-dir))
   (arguments
    `(#:tests? #f))
   (inputs
    `(("python" ,python)
      ("python-pyparsing" ,python-pyparsing)
      ("python-pyyaml" ,python-pyyaml)
      ("python-pyxdg" ,python-pyxdg)
      ("python-bytefmt" ,python-bytefmt)))
   (build-system python-build-system)
   (synopsis "Python Scripts for backup stuff")
   (description "Python Scripts for backup stuff")
   (home-page "https://gitlab.com/grumbel/scatterbackup")
   (license license:gpl3+)))

scatterbackup

;; EOF ;;
