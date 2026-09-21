// Binds the YAML metadata of cv.qmd to the `cv` template in typst-template.typ.
// Pandoc substitutes the template variables before Typst ever sees this file.
#show: cv.with(
  name: "$name$",
  surname: "$surname$",
  position: [$position$],
  address: [$address$],
  photo: "$profilepic$",
  email: "$email$",
  www: "$www$",
  github: "$github$",
  orcid: "$orcid$",
  scholar: "$scholar$",
  about: [$aboutme$],
  date: "$date$",
  keywords: ($for(keywords)$"$keywords$", $endfor$),
)
