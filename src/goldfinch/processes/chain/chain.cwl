$namespaces:
  s: https://schema.org/
$schemas:
- http://schema.org/version/9.0/schemaorg-current-http.rdf
baseCommand: python -m goldfinch.processes.chain.chain
class: CommandLineTool
cwlVersion: v1.2
hints:
  DockerRequirement:
    dockerPull: ghcr.io/bird-house/goldfinch:0.1.0
id: chain
inputs:
  input:
    inputBinding:
      position: 1
    type: File
  output:
    inputBinding:
      position: 2
    type: string
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
