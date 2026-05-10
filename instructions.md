AI Engineering Assignment - Scanned Medical Document Reconstruction

At LUNARTECH, we work on systems that go beyond simple OCR or text extraction. In many
real-world settings, especially in healthcare and document intelligence, it is not enough to
merely read text from a scanned file. The system must also understand the structure, context,
and meaning of the document, and reconstruct it into a clean, usable, and realistic output.

For this assignment, you will be given a small set of scanned documents. Your task is to build
a pipeline that can interpret these scans and generate a structured, visually faithful, and
professionally reconstructed output.

The goal is to evaluate your ability to work on real document intelligence problems using AI
engineering methods.

Build a system that takes as input one or more scanned medical documents and produces:

1. a structured understanding of the content,
2. a clean reconstructed version of the document,
3. and a final output that visually resembles the original document layout as closely as possible.

This is not only an OCR exercise. We want to assess whether your solution can combine:

- OCR / text extraction
- document layout understanding
- reasoning over noisy scanned content
- structured content generation
- visual reconstruction / format preservation
- practical engineering quality

## Input

You will receive a small sample set of scanned medical documents. These may include examples
such as:

- intake forms
- lab result sheets
- clinical summaries
- handwritten or semi-structured notes
- tables, boxes, headers, stamps, or form-like layouts

These files may contain:

- noise
- skew
- low resolution
- missing clarity
- inconsistent formatting
- partially difficult-to-read text

For safety and compliance, all documents used for the assignment should be synthetic,
anonymized, or fully de-identified.

## Task

Design and implement a system that processes the scanned inputs and generates a realistic
digital output.

Your system should aim to:

1. Extract the content

Read the scanned document and recover as much of the text and document structure as possible.

2. Understand the structure

Detect and interpret elements such as:

- headings
- subheadings
- patient or document metadata
- paragraphs
- tables
- field-value pairs
- checkboxes
- labels
- medical sections
- notes or comments

3. Reconstruct the document

Generate a clean, organized, and realistic digital version of the document that preserves the
structure and meaning of the original.

4. Preserve visual fidelity

The generated output should visually resemble the original as much as reasonably possible.
This includes:

- similar layout
- similar alignment
- section grouping
- spacing
- tables and boxes
- form structure
- hierarchy of information

The output should not just be correct in content. It should also be usable, realistic, and
presentation-ready.

## Expected Output

Your submission should produce the following for each input document:

### A. Structured extraction

A machine-readable representation of the document, for example in JSON or another structured
format.

This should include, where possible:

- document title
- metadata
- sections
- field-value pairs
- table contents
- notes
- extracted text blocks
- inferred layout structure

### B. Reconstructed document

A clean reconstructed version of the scanned document in one of the following formats:

- PDF
- HTML rendered to PDF
- DOCX
- any other clearly viewable format

### C. Visual output

A visually reconstructed output that resembles the original scan while being cleaner and
digitally usable.

### D. Short technical write-up

A brief explanation of:

- your approach
- the tools and models used
- how you handled OCR and layout
- how you handled uncertainty or ambiguity
- the main limitations of your solution
- what you would improve with more time

## Technical Expectations

You may use any tools or frameworks you consider appropriate. Examples include:

- Python
- OCR frameworks
- vision-language models
- LLMs
- layout detection tools
- PDF generation libraries
- HTML/CSS based rendering
- structured extraction pipelines

We are not evaluating you based on using a specific framework. We are evaluating how well you
solve the problem.

We care about engineering judgment, not just model usage.

## What We Are Looking For

We will evaluate submissions based on the following dimensions:

1. Accuracy of understanding
2. Structural reconstruction
3. Visual fidelity
4. Robustness
5. Engineering quality
6. Reasoning and problem-solving

Did the candidate demonstrate thoughtful decisions, tradeoff awareness, and a real
understanding of the problem?

## Deliverables

Please submit:

1. Source code
2. Instructions to run the project
3. Generated outputs for the sample documents
4. Structured extraction outputs
5. Short write-up or README
6. Optional: a short demo video or screenshots

## Time Expectation

Suggested time: 6-10 hours.

We are not expecting a perfect production-grade system. We are looking for:

- clear thinking
- strong execution
- practical engineering judgment
- evidence of technical depth

## Bonus Points

Bonus credit if your solution includes any of the following:

- confidence scoring
- handling of handwritten elements
- correction of OCR errors using context
- section classification
- table reconstruction
- visually strong document recreation
- modular pipeline design
- support for multiple document types
- use of AI to infer missing structure from noisy scans

## Important Notes

- Do not use real patient data unless it is explicitly de-identified and approved.
- If the scanned content is ambiguous, make reasonable assumptions and explain them.
- We value thoughtful systems over overly complex ones.
- A strong simple solution is better than an overly ambitious unstable one.

## Optional Short Version for a Public Job Post

Assignment: Scanned Medical Document Reconstruction

You will be given a small set of scanned medical documents. Your task is to build a system that
can:

- extract the content,
- understand the document structure,
- reconstruct the document in a clean digital format,
- and generate an output that visually resembles the original as closely as possible.

This is not just an OCR task. We want to assess your ability to combine document understanding,
AI reasoning, layout reconstruction, and practical engineering.

Deliverables:

- source code
- run instructions
- structured extraction output
- reconstructed final documents
- short explanation of your approach

## Confidentiality and IP Protection

All materials provided as part of this assignment, including scanned documents, sample inputs,
instructions, evaluation criteria, internal examples, and any related context, are confidential
and proprietary to LUNARTECH.

Candidates are not permitted to publish, upload, distribute, share, reproduce, or make publicly
available any part of the assignment materials or their solution outputs. This includes, but is
not limited to:

- public GitHub repositories
- portfolio websites
- LinkedIn posts
- social media
- blogs
- public demos
- model-sharing platforms
- forums
- third-party communities
- or any other public or private distribution channel not expressly approved by LUNARTECH

All code, outputs, reconstructions, structured extractions, generated documents, and technical
materials created in response to this assignment must be shared only with LUNARTECH through
the official submission process.

The assignment materials are provided solely for the purpose of candidate evaluation.
Candidates may not reuse, commercialize, modify for public distribution, or repurpose the
materials for any other personal, academic, professional, or commercial use without prior
written permission from LUNARTECH.

Because the assignment involves medical-style documents and proprietary document-intelligence
evaluation materials, candidates must treat all provided files and generated outputs as
confidential. Even if the documents are synthetic, anonymized, or fictional, they remain
protected evaluation materials and must not be disclosed externally.

By accepting and completing this assignment, the candidate agrees to keep all assignment
materials, generated outputs, and related technical work confidential and to respect
LUNARTECH's intellectual property rights.

Important confidentiality note:

This assignment and all related materials are confidential and IP-protected. Candidates may not
upload the assignment, source files, generated outputs, or solution materials to GitHub,
portfolio websites, social media, blogs, public demos, or any external platform. All work must
be submitted privately to LUNARTECH and used only for candidate evaluation.
