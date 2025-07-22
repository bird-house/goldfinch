$namespaces:
  s: https://schema.org/
$schemas:
- http://schema.org/version/9.0/schemaorg-current-http.rdf
baseCommand: python /home/francis/dev/goldfinch/src/goldfinch/processes/indicator/hdd.py
class: CommandLineTool
cwlVersion: v1.2
hints:
  DockerRequirement:
    dockerPull: ghcr.io/bird-house/goldfinch:0.1.0
id: hdd
inputs:
  input:
    type:
    - 'null'
    - inputBinding:
        position: 1
        prefix: -i
      items: string
      type: array
  output:
    inputBinding:
      position: 2
      prefix: -o
    type: string?
  verbose:
    inputBinding:
      position: 3
      prefix: -v
    type: None?
  dask_nthreads:
    inputBinding:
      position: 4
      prefix: --dask-nthreads
    type: None?
  dask_maxmem:
    inputBinding:
      position: 5
      prefix: --dask-maxmem
    type: string?
  chunks:
    inputBinding:
      position: 6
      prefix: --chunks
    type: string?
  engine:
    inputBinding:
      position: 7
      prefix: --engine
    type: string?
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
