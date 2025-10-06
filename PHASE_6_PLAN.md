# Phase 6: MCP Integration - Implementation Plan

**Version**: 1.0.0
**Status**: Planning
**Started**: 2025-10-06
**Estimated Duration**: 3-5 days

---

## Overview

Phase 6 integrates all Phase 5 Knowledge Graph tools into the MCP (Model Context Protocol) server, making them accessible through slash commands in Claude Code. This provides a unified command-line interface for graph building, querying, visualization, and analysis.

### Goals

1. **Integrate Phase 5 Tools**: Add all 11 Phase 5 components to MCP server
2. **Slash Commands**: Create intuitive commands for graph operations
3. **Unified Workflow**: Enable end-to-end graph building and analysis from Claude Code
4. **Documentation**: Provide comprehensive command documentation

---

## Architecture

### Current MCP Server Status

**Existing Commands** (Phase 3-4):
- `/analyze-jsp` - JSP analysis
- `/analyze-controller` - Controller analysis
- `/analyze-service` - Service analysis
- `/analyze-mybatis` - MyBatis mapper analysis
- `/analyze-all` - Batch analysis of all components
- `/find-chain` - Find dependency chains
- `/impact-analysis` - Impact analysis (Phase 4)

**MCP Server Version**: 0.4.4-alpha

### Phase 6 Integration Architecture

```
┌─────────────────────────────────────────────────────────┐
│              MCP Server (Phase 6 Enhanced)              │
├─────────────────────────────────────────────────────────┤
│  Phase 3-4 Commands (Existing)                          │
│  ✓ analyze-jsp, controller, service, mybatis            │
│  ✓ analyze-all, find-chain, impact-analysis             │
├─────────────────────────────────────────────────────────┤
│  Phase 5 Graph Commands (NEW)                           │
│  • build-graph       - Build code-based graph           │
│  • merge-graphs      - Merge code + LLM graphs          │
│  • visualize-graph   - Generate visualizations          │
│  • query-path        - Find paths between nodes         │
│  • find-dependencies - Get node dependencies            │
│  • analyze-impact    - Enhanced impact analysis         │
│  • find-critical     - Critical node detection          │
│  • graph-stats       - Graph statistics                 │
└─────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│              Phase 5 Tools Integration                   │
├─────────────────────────────────────────────────────────┤
│  Layer 1: Code-Based                                     │
│  • GraphDataLoader   • GraphNodeBuilder                 │
│  • GraphEdgeBuilder  • CodeGraphBuilder                 │
├─────────────────────────────────────────────────────────┤
│  Layer 2: LLM-Based (Optional)                          │
│  • SemanticCache     • LLMQueryEngine                   │
│  • URLMatcher        • CompletenessScanner              │
├─────────────────────────────────────────────────────────┤
│  Layer 3: Merging                                        │
│  • GraphMerger                                           │
├─────────────────────────────────────────────────────────┤
│  Layer 4: Visualization                                  │
│  • GraphVisualizer                                       │
├─────────────────────────────────────────────────────────┤
│  Layer 5: Querying                                       │
│  • GraphQueryEngine                                      │
└─────────────────────────────────────────────────────────┘
```

---

## Phase 6 Sub-Tasks

### Phase 6.1: Graph Building Commands ✨

**Duration**: 1 day

#### 6.1.1: Build Graph Command

**Command**: `/build-graph` (alias: `/graph`)

**Purpose**: Build code-based knowledge graph from Phase 3 analysis results.

**Parameters**:
- `--base-dir` (optional): Base directory for analysis results (default: `output/analysis`)
- `--output` (optional): Output path for graph JSON (default: `output/graph/code_based_graph.json`)
- `--export-stats` (optional): Export statistics (default: true)
- `--export-low-conf` (optional): Export low confidence edges (default: true)

**Implementation**: `mcp_server/commands/build_graph_cmd.py`

**Example**:
```
/build-graph
/build-graph --base-dir=output/analysis --output=output/graph/my_graph.json
```

**Output**:
- Graph JSON file
- Statistics JSON
- Low confidence edges JSON
- Console summary

---

#### 6.1.2: Graph Statistics Command

**Command**: `/graph-stats` (alias: `/stats`)

**Purpose**: Display graph statistics and metrics.

**Parameters**:
- `--graph-file` (optional): Path to graph JSON (default: latest built graph)
- `--detailed` (optional): Show detailed breakdown (default: false)

**Implementation**: `mcp_server/commands/graph_stats_cmd.py`

**Example**:
```
/graph-stats
/graph-stats --detailed
```

**Output**:
- Total nodes/edges
- Nodes by type
- Edges by type
- Density, connectivity
- Orphan nodes
- Coverage metrics

---

### Phase 6.2: Graph Visualization Commands 🎨

**Duration**: 1 day

#### 6.2.1: Visualize Graph Command

**Command**: `/visualize-graph` (alias: `/viz`, `/visualize`)

**Purpose**: Generate interactive or static graph visualizations.

**Parameters**:
- `--format` (required): Visualization format (`pyvis`, `mermaid`, or `both`) (default: `both`)
- `--graph-file` (optional): Path to graph JSON (default: latest)
- `--output-dir` (optional): Output directory (default: `output/graph`)
- `--max-nodes` (optional): Max nodes for Mermaid (default: 100)
- `--physics` (optional): Enable PyVis physics (default: true)
- `--hierarchical` (optional): Use hierarchical layout (default: false)

**Implementation**: `mcp_server/commands/visualize_graph_cmd.py`

**Example**:
```
/visualize-graph
/visualize-graph --format=pyvis
/visualize-graph --format=mermaid --max-nodes=50
/visualize-graph --hierarchical
```

**Output**:
- PyVis HTML: `output/graph/interactive.html`
- Mermaid diagram: `output/graph/diagram.mermaid.md`
- Console: File paths and instructions

---

#### 6.2.2: Extract Subgraph Command

**Command**: `/extract-subgraph` (alias: `/subgraph`)

**Purpose**: Extract and visualize a subgraph.

**Parameters**:
- `--node-types` (optional): Comma-separated node types (e.g., `CONTROLLER,SERVICE,MAPPER`)
- `--start-nodes` (optional): Comma-separated starting nodes
- `--max-depth` (optional): Maximum traversal depth
- `--output` (optional): Output graph JSON path
- `--visualize` (optional): Auto-visualize subgraph (default: true)

**Implementation**: `mcp_server/commands/extract_subgraph_cmd.py`

**Example**:
```
/extract-subgraph --node-types=CONTROLLER,SERVICE,MAPPER
/extract-subgraph --start-nodes=UserController --max-depth=3
/extract-subgraph --start-nodes=user_list.jsp --visualize
```

**Output**:
- Subgraph JSON
- Optional visualization (PyVis HTML)
- Console summary

---

### Phase 6.3: Graph Querying Commands 🔍

**Duration**: 1-2 days

#### 6.3.1: Query Path Command

**Command**: `/query-path` (alias: `/path`, `/find-path`)

**Purpose**: Find paths between two nodes.

**Parameters**:
- `--source` (required): Source node ID
- `--target` (required): Target node ID
- `--all-paths` (optional): Find all paths (default: false, finds shortest)
- `--max-length` (optional): Max path length for all-paths (default: 10)
- `--relation-types` (optional): Comma-separated relation types to filter
- `--weighted` (optional): Use weighted shortest path (default: false)

**Implementation**: `mcp_server/commands/query_path_cmd.py`

**Example**:
```
/query-path --source=user_list.jsp --target=USERS_TABLE
/query-path --source=UserController --target=USERS_TABLE --all-paths
/query-path --source=UserService --target=UserMapper --relation-types=CALLS
```

**Output**:
- Path(s) found
- Path length
- Confidence score (for weighted)
- Visualization of path

---

#### 6.3.2: Find Dependencies Command

**Command**: `/find-dependencies` (alias: `/deps`, `/dependencies`)

**Purpose**: Find upstream dependencies or downstream dependents.

**Parameters**:
- `--node` (required): Node ID
- `--direction` (required): `upstream` (dependencies) or `downstream` (dependents)
- `--max-depth` (optional): Maximum depth (default: 3)
- `--visualize` (optional): Visualize dependency tree (default: true)

**Implementation**: `mcp_server/commands/find_dependencies_cmd.py`

**Example**:
```
/find-dependencies --node=UserService.listUsers --direction=upstream
/find-dependencies --node=USERS_TABLE --direction=downstream --max-depth=5
```

**Output**:
- Total dependencies/dependents
- Dependency list with layers
- Optional tree visualization

---

#### 6.3.3: Dependency Chain Command (Enhanced)

**Command**: `/dependency-chain` (alias: `/chain`)

**Purpose**: Find full dependency chain from starting node.

**Parameters**:
- `--start-node` (required): Starting node ID
- `--node-type-order` (optional): Custom type order (comma-separated)
- `--visualize` (optional): Visualize chains (default: true)

**Implementation**: Enhance existing `/find-chain` command

**Example**:
```
/dependency-chain --start-node=user_list.jsp
/dependency-chain --start-node=UserController --node-type-order=CONTROLLER,SERVICE,MAPPER,SQL
```

**Output**:
- All dependency chains
- Visualization of chains

---

#### 6.3.4: Impact Analysis Command (Enhanced)

**Command**: `/analyze-impact` (alias: `/impact`)

**Purpose**: Analyze impact of changing a node (enhanced from Phase 4).

**Parameters**:
- `--node` (required): Node ID to analyze
- `--show-severity` (optional): Show severity breakdown (default: true)
- `--visualize` (optional): Visualize impacted nodes (default: true)

**Implementation**: Enhance existing `/impact-analysis` to use GraphQueryEngine

**Example**:
```
/analyze-impact --node=UserService.updateUser
/analyze-impact --node=USERS_TABLE
```

**Output**:
- Total affected nodes
- Impact score
- Severity (CRITICAL/HIGH/MEDIUM/LOW)
- Affected nodes by severity
- Visualization

---

#### 6.3.5: Find Critical Nodes Command

**Command**: `/find-critical` (alias: `/critical`, `/critical-nodes`)

**Purpose**: Find critical nodes in the graph.

**Parameters**:
- `--top-n` (optional): Number of top critical nodes (default: 10)
- `--min-score` (optional): Minimum criticality score (default: 0.5)
- `--visualize` (optional): Visualize critical nodes (default: true)

**Implementation**: `mcp_server/commands/find_critical_cmd.py`

**Example**:
```
/find-critical
/find-critical --top-n=5
/find-critical --min-score=0.7
```

**Output**:
- Top N critical nodes
- Criticality scores
- Breakdown: degree, betweenness, impact
- Visualization highlighting critical nodes

---

### Phase 6.4: Graph Merging Commands 🔀

**Duration**: 1 day

#### 6.4.1: Merge Graphs Command

**Command**: `/merge-graphs` (alias: `/merge`)

**Purpose**: Merge code-based and LLM-verified graphs.

**Parameters**:
- `--code-graph` (required): Path to code-based graph JSON
- `--llm-graph` (required): Path to LLM-verified graph JSON
- `--output` (optional): Output path for merged graph (default: `output/graph/merged_graph.json`)
- `--agreement-bonus` (optional): Confidence bonus for agreement (default: 0.1)
- `--llm-penalty` (optional): Confidence penalty for LLM-only (default: 0.9)
- `--show-conflicts` (optional): Show detailed conflicts (default: true)

**Implementation**: `mcp_server/commands/merge_graphs_cmd.py`

**Example**:
```
/merge-graphs --code-graph=output/graph/code_based.json --llm-graph=output/graph/llm_verified.json
/merge-graphs --code-graph=graph1.json --llm-graph=graph2.json --agreement-bonus=0.15
```

**Output**:
- Merged graph JSON
- Merge report JSON
- Console summary: conflicts detected, resolution applied
- Conflict details

---

### Phase 6.5: Complete Workflow Command 🚀

**Duration**: 0.5 day

#### 6.5.1: Build Complete Graph Command

**Command**: `/build-complete-graph` (alias: `/complete`)

**Purpose**: Execute complete workflow from analysis to visualization.

**Parameters**:
- `--analyze` (optional): Run Phase 3 analysis first (default: false)
- `--base-dir` (optional): Base directory (default: `output/analysis`)
- `--include-llm` (optional): Include LLM verification (default: false)
- `--visualize` (optional): Generate visualizations (default: true)
- `--format` (optional): Visualization format (default: `both`)

**Implementation**: `mcp_server/commands/build_complete_graph_cmd.py`

**Example**:
```
/build-complete-graph
/build-complete-graph --analyze --visualize
/build-complete-graph --include-llm --format=pyvis
```

**Workflow**:
1. [Optional] Run Phase 3 analysis
2. Build code-based graph
3. [Optional] LLM verification and merge
4. [Optional] Generate visualizations
5. Display statistics and critical nodes

**Output**:
- Complete graph (code or merged)
- Visualizations
- Statistics
- Critical nodes summary

---

## Command Organization

### Command Categories

**Analysis** (Phase 3-4, existing):
- `/analyze-jsp`
- `/analyze-controller`
- `/analyze-service`
- `/analyze-mybatis`
- `/analyze-all`

**Graph Building** (Phase 6.1):
- `/build-graph`
- `/graph-stats`

**Graph Visualization** (Phase 6.2):
- `/visualize-graph`
- `/extract-subgraph`

**Graph Querying** (Phase 6.3):
- `/query-path`
- `/find-dependencies`
- `/dependency-chain`
- `/analyze-impact`
- `/find-critical`

**Graph Merging** (Phase 6.4):
- `/merge-graphs`

**Complete Workflow** (Phase 6.5):
- `/build-complete-graph`

---

## Implementation Plan

### Day 1: Graph Building Commands
- ✅ Morning: `/build-graph` command
- ✅ Afternoon: `/graph-stats` command
- ✅ Evening: Testing and documentation

### Day 2: Visualization Commands
- ✅ Morning: `/visualize-graph` command
- ✅ Afternoon: `/extract-subgraph` command
- ✅ Evening: Testing and documentation

### Day 3: Querying Commands (Part 1)
- ✅ Morning: `/query-path` command
- ✅ Afternoon: `/find-dependencies` command
- ✅ Evening: Testing and documentation

### Day 4: Querying Commands (Part 2) + Merging
- ✅ Morning: `/find-critical` command
- ✅ Afternoon: `/merge-graphs` command
- ✅ Evening: Testing and documentation

### Day 5: Complete Workflow + Integration
- ✅ Morning: `/build-complete-graph` command
- ✅ Afternoon: Integration testing
- ✅ Evening: Documentation and review

---

## Testing Strategy

### Unit Tests
- Test each command independently
- Mock Phase 5 tools
- Verify parameter parsing
- Check output format

### Integration Tests
- End-to-end workflow tests
- Use sample project data
- Verify graph building and querying
- Test visualization generation

### Manual Testing
- Test all commands via Claude Code
- Verify slash command aliases
- Check error handling
- Validate output files

---

## Documentation

### Command Documentation
- README.md: Add Phase 6 commands section
- COMMANDS.md: Comprehensive command reference (NEW)
- Each command: Inline help text

### User Guide
- Workflow examples
- Common use cases
- Troubleshooting guide

### API Documentation
- MCP server API updates
- Tool registration examples
- Command implementation guide

---

## Success Criteria

✅ **All Commands Implemented**
- 8 new commands + 2 enhanced commands
- All with aliases
- Comprehensive parameter support

✅ **Integration Complete**
- All Phase 5 tools accessible via MCP
- Consistent command interface
- Error handling and validation

✅ **Documentation Complete**
- Command reference
- Usage examples
- Workflow guide

✅ **Testing Complete**
- Unit tests for all commands
- Integration tests pass
- Manual testing successful

---

## Next Steps After Phase 6

1. **Phase 7**: Semantic Enhancement (LLM-based business logic analysis)
2. **Phase 0**: Validation Strategy (small, medium, large scale testing)
3. **Production**: Deploy as service/CLI tool

---

## Dependencies

### External Libraries (already installed)
- networkx>=3.0
- pyvis>=0.3.2
- anthropic (for LLM features)

### Phase 5 Components (all complete)
- GraphDataLoader
- GraphNodeBuilder
- GraphEdgeBuilder
- CodeGraphBuilder
- GraphVisualizer
- GraphQueryEngine
- GraphMerger
- SemanticCache
- LLMQueryEngine
- URLMatcher
- CompletenessScanner

---

**Status**: Planning Complete - Ready for Implementation
**Last Updated**: 2025-10-06
**Next**: Start with Phase 6.1 (Graph Building Commands)
