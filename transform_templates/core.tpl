;; core.tpl — Transformation templates for CS 5260 Part 1

;; Housing Template
(TRANSFORM C
  (INPUTS
    (Population            5)
    (MetallicElements      1)
    (Timber                5)
    (MetallicAlloys        3))
  (OUTPUTS
    (Housing               1)
    (HousingWaste          1)
    (Population            5))
)

;; Alloys Template
(TRANSFORM C
  (INPUTS
    (Population            1)
    (MetallicElements      2))
  (OUTPUTS
    (Population            1)
    (MetallicAlloys        1)
    (MetallicAlloysWaste   1))
)

;; Electronics Template
(TRANSFORM C
  (INPUTS
    (Population            1)
    (MetallicElements      3)
    (MetallicAlloys        2))
  (OUTPUTS
    (Population            1)
    (Electronics           2)
    (ElectronicsWaste      1))
)
