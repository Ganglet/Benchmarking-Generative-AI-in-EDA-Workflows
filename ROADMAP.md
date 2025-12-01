# Development Roadmap

This document outlines the development roadmap for the Benchmarking Generative AI in EDA Workflows project.

## Phase 1: Core Implementation ✅

**Status**: Completed

- [x] Pipeline infrastructure
- [x] Model integration (Ollama/HF)
- [x] Starter dataset (5 tasks)
- [x] Statistical analysis
- [x] Visualization module

**Deliverables**:
- Basic evaluation pipeline
- Support for multiple model backends
- Initial benchmark results

---

## Phase 2: Enhanced Prompting & Post-Processing ✅

**Status**: Completed

- [x] Constrained prompts with exact module/port specifications
- [x] Comprehensive examples for all task types (20 tasks)
- [x] Enhanced post-processing with FSM/mixed template generation
- [x] Sequential normalization for reliable sequential designs
- [x] Category-specific scaffolding to prevent truncation
- [x] Full 20-task benchmark evaluation (8th benchmark)

**Key Achievements**:
- **FSM Breakthrough**: StarCoder2 achieves 66.7% syntax validity for FSM tasks (previously 0%)
- **Mixed Design Success**: StarCoder2 achieves 66.7% functional correctness on priority encoder
- **Sequential Expansion**: All models handle expanded sequential library (T flip-flop, shift register, PIPO register)
- **Overall Improvement**: 70% syntax validity (Llama-3), 55% (StarCoder2), 65% (TinyLlama)

**Deliverables**:
- Enhanced post-processing pipeline
- 20-task benchmark dataset
- Comprehensive benchmark results (Benchmarks 2-8)

---

## Phase 3: Dataset Expansion ✅ (Concluded)

**Status**: Completed – scope intentionally capped at 50 curated tasks

- [x] Expand to 50 tasks (Benchmark 10) ✅
- [ ] Additional expansion (de-scoped by design)

**Current Progress**:
- ✅ 50 tasks completed (23 combinational, 14 sequential, 8 FSM, 5 mixed)
- ✅ Phase 4 pipeline validated on 50-task dataset (450 total generations)
- 🛑 Expansion beyond 50 tasks paused to focus on depth, analysis quality, and publication prep

**Next Steps**:
- Package and document the final 50-task dataset for release
- Double-down on FSM and mixed design evaluation strategies within the existing scope
- Capture lessons learned + recommendations for future contributors

**Deliverables**:
- Finalized 50-task dataset package + documentation
- Benchmark 10 (final dataset) analysis
- Guidance for future extensions (should expansion resume)

---

## Phase 4: Advanced Features 📋

**Status**: Partially Completed (Semantic-Aware Iterative Refinement ✅)

### Completed ✅
- [x] Semantic-aware iterative refinement (Benchmark 9-10)
- [x] Waveform analysis
- [x] Formal verification (optional)
- [x] AST-based code repair
- [x] Confidence tracking
- [x] Adaptive stopping
- [x] Task tiering for efficiency

### Planned 📋
- [ ] Fault injection for testbench evaluation
- [ ] Prompt template variations
- [ ] Coverage analysis
- [ ] Error taxonomy
- [ ] FSM functional correctness refinement

**Priority Items**:
1. **FSM Functional Correctness**: Current bottleneck (0% simulation despite syntax validity)
2. **Error Taxonomy**: Systematic error classification
3. **Coverage Analysis**: Test coverage metrics

**Deliverables**:
- Advanced evaluation features
- Error taxonomy documentation
- Coverage analysis tools

---

## Phase 5: Full Benchmark & Publication 📋

**Status**: Planned

- [ ] Run complete experiments on the finalized 50-task dataset
- [ ] Generate publication-ready results
- [ ] Write research paper
- [ ] Prepare supplementary materials
- [ ] Open-source release

**Milestones**:
1. Publish the 50-task dataset package + accompanying documentation
2. Run/full benchmark suite on the final dataset
3. Statistical analysis and visualization
4. Paper writing
5. Submission

**Deliverables**:
- Research paper
- Complete benchmark results
- Public dataset release
- Open-source codebase

---

## Long-Term Vision

### Research Directions
1. **Model Fine-Tuning**: Fine-tune models on HDL corpus
2. **Prompt Engineering**: Systematic prompt optimization research
3. **Ensemble Methods**: Multi-model ensemble approaches
4. **Synthesis Integration**: Synthesis quality metrics and optimization

### Tool Integration
1. **Synthesis Quality**: Yosys integration for gate count, area
2. **Timing Analysis**: Timing constraint validation
3. **Power Estimation**: Power consumption metrics
4. **Formal Verification**: Enhanced formal verification integration

### Community Engagement
1. **Open-Source Release**: Public repository
2. **Documentation**: Comprehensive user and developer docs
3. **Tutorials**: Step-by-step guides
4. **Workshops**: Community workshops and presentations

---

## Current Priorities (Q1 2026)

### High Priority
1. ✅ Complete 50-task dataset validation (Done)
2. Publish final 50-task dataset package & release notes
3. FSM functional correctness research
4. Error taxonomy development

### Medium Priority
1. Coverage analysis implementation
2. Prompt template variation study
3. Documentation + reproducibility improvements
4. Mixed-design logic repair experiments

### Low Priority
1. Synthesis quality integration
2. Ensemble method exploration
3. Fine-tuning experiments

---

## Success Metrics

### Dataset
- [x] 50 tasks validated ✅ (final scope)
- [ ] Additional expansion (paused indefinitely)

### Performance
- [x] >70% syntax validity (achieved)
- [x] >60% simulation pass rate for best model (achieved)
- [ ] >50% FSM functional correctness
- [ ] >70% mixed design functional correctness

### Research
- [x] 10 benchmarks completed ✅
- [ ] Research paper submitted
- [ ] Open-source release
- [ ] Community adoption

---

## Contributing to the Roadmap

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on contributing to the project.

**Areas Needing Contribution**:
- Dataset expansion (new tasks)
- FSM functional correctness research
- Error taxonomy development
- Documentation improvements
- Testing and validation

---

## Timeline

### Q4 2025
- ✅ Phase 4 implementation (Benchmark 9)
- ✅ 50-task dataset expansion (Benchmark 10)
- ✅ Documentation structure

### Q1 2026
- Publish final 50-task dataset package
- FSM functional correctness research
- Error taxonomy development

### Q2 2026
- Coverage analysis implementation
- Prompt template variation study
- Mixed/mixed-complex logic repair experiments

### Q3 2026
- Full benchmark execution on final 50-task dataset
- Draft publication + supplementary analyses
- Community feedback loop on final dataset

### Q4 2026
- Paper submission
- Open-source release
- Community engagement

---

**Last Updated**: November 2025  
**Next Review**: January 2026

