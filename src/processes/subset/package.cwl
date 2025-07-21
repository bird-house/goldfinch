cwlVersion: "v1.2"
class: CommandLineTool
label: "Subset"
baseCommand: [python3, poly_subset.py]
inputs:
  input_file:
    type: File
    inputBinding:
      position: 1
      prefix: "--input-file"
  output_file:
    type: File
    inputBinding:
      position: 2
      prefix: "--output-file"
  subset_size:
    type: int
    inputBinding:
      position: 3
      prefix: "--subset-size"
