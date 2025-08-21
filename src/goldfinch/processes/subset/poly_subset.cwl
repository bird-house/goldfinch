$namespaces:
  s: https://schema.org/
$schemas:
- http://schema.org/version/9.0/schemaorg-current-http.rdf
baseCommand: python -m goldfinch.processes.subset.poly_subset
class: CommandLineTool
cwlVersion: v1.2
hints:
  DockerRequirement:
    dockerPull: ghcr.io/bird-house/goldfinch:0.1.0
id: poly_subset
inputs:
  buffer:
    inputBinding:
      position: 5
      prefix: -b
    type: None?
  end:
    inputBinding:
      position: 7
      prefix: -e
    type: string?
  first_level:
    inputBinding:
      position: 8
      prefix: -f
    type: string?
  help:
    inputBinding:
      position: 1
      prefix: -h
    type: boolean?
  input:
    inputBinding:
      position: 2
      prefix: -i
    type: string?
  last_level:
    inputBinding:
      position: 9
      prefix: -l
    type: string?
  output:
    inputBinding:
      position: 3
      prefix: -o
    type: File?
  poly:
    inputBinding:
      position: 4
      prefix: -p
    type: File?
  start:
    inputBinding:
      position: 6
      prefix: -s
    type: string?
  verbose:
    inputBinding:
      position: 10
      prefix: -v
    type: None?
outputs:
  results:
    outputBinding:
      glob: .
    type: Directory
requirements:
  EnvVarRequirement:
    envDef: {}
  ResourceRequirement: {}
stderr: std.err
stdout: std.out
