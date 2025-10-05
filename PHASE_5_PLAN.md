# Phase 5: Knowledge Graph Building - Implementation Plan

**Version**: 0.5.0-alpha
**Status**: Planning
**Started**: 2025-10-05
**Estimated Duration**: 2-3 weeks

---

## Overview

Phase 5 builds the complete knowledge graph by combining:
1. **Code-based relationships** (100% accurate, from Phase 3 analyzers)
2. **LLM-verified relationships** (fill gaps, verify ambiguous connections)
3. **Merged unified graph** (conflict resolution, confidence scoring)
4. **Interactive visualization** (PyVis HTML, Mermaid, GraphML)

**Strategy**: Hybrid two-layer approach for accuracy + completeness

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│           Phase 3 Analysis Results                       │
│  (JSP, Controller, Service, Mapper, SQL, DB Schema)     │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
┌──────────────────┐      ┌──────────────────┐
│ Layer 1: Code    │      │ Layer 2: LLM     │
│ Graph Builder    │      │ Graph Builder    │
│                  │      │                  │
│ • 100% certain   │      │ • Gap filling    │
│ • Direct parsing │      │ • URL matching   │
│ • High conf      │      │ • Verification   │
└────────┬─────────┘      └────────┬─────────┘
         │                         │
         └──────────┬──────────────┘
                    ▼
         ┌──────────────────────┐
         │   Graph Merger       │
         │                      │
         │ • Conflict resolution│
         │ • Confidence scoring │
         │ • Relationship rules │
         └──────────┬───────────┘
                    ▼
         ┌──────────────────────┐
         │   Unified Graph      │
         │   (NetworkX)         │
         └──────────┬───────────┘
                    ▼
         ┌──────────────────────┐
         │   Visualization      │
         │                      │
         │ • PyVis HTML         │
         │ • Mermaid diagrams   │
         │ • GraphML export     │
         └──────────────────────┘
```

---

## Sub-Phases Breakdown

### Phase 5.1: Graph Builder - Layer 1 (Code-based) ⏳

**Goal**: Build graph from 100% certain code-based relationships

**Duration**: 3-4 days

**Dependencies**: Phase 3 complete (all analyzers working)

#### 5.1.1: Data Loader
- [ ] **Input Files**:
  ```python
  {
    "jsp": "output/analysis/jsp/*.json",
    "controllers": "output/analysis/controllers/*.json",
    "services": "output/analysis/services/*.json",
    "mappers": "output/analysis/mappers/*.json",
    "db_schema": "output/db_schema.json",
    "procedures": "output/analysis/procedures/*.json"
  }
  ```

- [ ] **Loader Implementation** (`mcp_server/tools/graph_data_loader.py`):
  ```python
  class GraphDataLoader:
      def load_all_analysis_results(self, base_dir: str) -> Dict[str, Any]:
          """Load all Phase 3 analysis results"""

      def load_jsp_analysis(self) -> List[Dict]:
          """Load JSP analysis results"""

      def load_controller_analysis(self) -> List[Dict]:
          """Load Controller analysis results"""

      def load_service_analysis(self) -> List[Dict]:
          """Load Service analysis results"""

      def load_mybatis_analysis(self) -> List[Dict]:
          """Load MyBatis Mapper analysis results"""

      def load_db_schema(self) -> Dict:
          """Load Oracle DB schema"""

      def load_procedure_analysis(self) -> List[Dict]:
          """Load Procedure analysis results"""
  ```

- [ ] **Validation**:
  - Check all required files exist
  - Validate JSON structure
  - Report missing or corrupt files
  - Continue with partial data if possible

#### 5.1.2: Node Creation
- [ ] **Node Types** (11 types):
  ```python
  NODE_TYPES = {
      "JSP": {"color": "#FF6B6B", "shape": "box"},
      "CONTROLLER": {"color": "#4ECDC4", "shape": "ellipse"},
      "SERVICE": {"color": "#45B7D1", "shape": "ellipse"},
      "MAPPER": {"color": "#96CEB4", "shape": "ellipse"},
      "TABLE": {"color": "#FFEAA7", "shape": "database"},
      "VIEW": {"color": "#DFE6E9", "shape": "database"},
      "PROCEDURE": {"color": "#A29BFE", "shape": "hexagon"},
      "TRIGGER": {"color": "#FD79A8", "shape": "diamond"},
      "ORACLE_JOB": {"color": "#FDCB6E", "shape": "star"},
      "SQL": {"color": "#E17055", "shape": "box"},
      "AJAX_CALL": {"color": "#74B9FF", "shape": "dot"}
  }
  ```

- [ ] **Node Builder** (`mcp_server/tools/graph_node_builder.py`):
  ```python
  class NodeBuilder:
      def create_jsp_nodes(self, jsp_data: List[Dict]) -> List[Node]:
          """Create JSP nodes with metadata"""

      def create_controller_nodes(self, controller_data: List[Dict]) -> List[Node]:
          """Create Controller method nodes"""

      def create_service_nodes(self, service_data: List[Dict]) -> List[Node]:
          """Create Service method nodes"""

      def create_mapper_nodes(self, mapper_data: List[Dict]) -> List[Node]:
          """Create Mapper method nodes"""

      def create_database_nodes(self, db_schema: Dict) -> List[Node]:
          """Create Table, View, Procedure, Trigger, Job nodes"""

      def create_sql_nodes(self, mapper_data: List[Dict]) -> List[Node]:
          """Create SQL statement nodes from Mapper XML"""
  ```

- [ ] **Node Attributes**:
  - Unique ID (e.g., `"JSP:user/list.jsp"`, `"CONTROLLER:UserController.getList"`)
  - Type (from NODE_TYPES)
  - Display name
  - Full path/location
  - Metadata (depends on type)

#### 5.1.3: Edge Creation (High Confidence)
- [ ] **Edge Types & Confidence**:
  ```python
  EDGE_TYPES = {
      "INCLUDES": {"confidence": 1.0, "source": "static_include"},
      "CALLS": {"confidence": 0.6-1.0, "source": "url_pattern"},
      "INVOKES": {"confidence": 1.0, "source": "autowired"},
      "USES": {"confidence": 1.0, "source": "dependency_injection"},
      "EXECUTES": {"confidence": 1.0, "source": "mapper_xml"},
      "QUERIES": {"confidence": 0.8-1.0, "source": "sql_parse"},
      "MODIFIES": {"confidence": 0.8-1.0, "source": "sql_parse"},
      "CALLS_PROCEDURE": {"confidence": 1.0, "source": "callable_statement"},
      "TRIGGERED_BY": {"confidence": 1.0, "source": "db_trigger"},
      "SCHEDULED_BY": {"confidence": 1.0, "source": "oracle_job"}
  }
  ```

- [ ] **Edge Builder** (`mcp_server/tools/graph_edge_builder.py`):
  ```python
  class EdgeBuilder:
      def build_jsp_includes(self, jsp_nodes: List[Node]) -> List[Edge]:
          """JSP -> JSP (INCLUDES) - confidence: 1.0"""

      def build_jsp_to_controller(self, jsp_nodes: List[Node],
                                    controller_nodes: List[Node]) -> List[Edge]:
          """JSP -> CONTROLLER (CALLS) - confidence: 0.6-0.9"""
          # URL pattern matching (may need Layer 2 verification)

      def build_controller_to_service(self, controller_nodes: List[Node],
                                        service_nodes: List[Node]) -> List[Edge]:
          """CONTROLLER -> SERVICE (INVOKES) - confidence: 1.0"""

      def build_service_to_mapper(self, service_nodes: List[Node],
                                    mapper_nodes: List[Node]) -> List[Edge]:
          """SERVICE -> MAPPER (USES) - confidence: 1.0"""

      def build_mapper_to_sql(self, mapper_nodes: List[Node],
                               sql_nodes: List[Node]) -> List[Edge]:
          """MAPPER -> SQL (EXECUTES) - confidence: 1.0"""

      def build_sql_to_tables(self, sql_nodes: List[Node],
                               table_nodes: List[Node]) -> List[Edge]:
          """SQL -> TABLE (QUERIES/MODIFIES) - confidence: 0.8-1.0"""

      def build_sql_to_procedures(self, sql_nodes: List[Node],
                                    procedure_nodes: List[Node]) -> List[Edge]:
          """SQL -> PROCEDURE (CALLS_PROCEDURE) - confidence: 1.0"""

      def build_trigger_edges(self, trigger_nodes: List[Node],
                               procedure_nodes: List[Node]) -> List[Edge]:
          """TRIGGER -> PROCEDURE (TRIGGERED_BY) - confidence: 1.0"""

      def build_job_edges(self, job_nodes: List[Node],
                           procedure_nodes: List[Node]) -> List[Edge]:
          """ORACLE_JOB -> PROCEDURE (SCHEDULED_BY) - confidence: 1.0"""
  ```

#### 5.1.4: Graph Construction
- [ ] **NetworkX Graph** (`mcp_server/tools/code_graph_builder.py`):
  ```python
  class CodeGraphBuilder:
      def __init__(self):
          self.graph = nx.DiGraph()
          self.loader = GraphDataLoader()
          self.node_builder = NodeBuilder()
          self.edge_builder = EdgeBuilder()

      def build_graph(self, base_dir: str) -> nx.DiGraph:
          """Build complete code-based graph"""
          # 1. Load data
          data = self.loader.load_all_analysis_results(base_dir)

          # 2. Create nodes
          all_nodes = self._create_all_nodes(data)

          # 3. Add nodes to graph
          for node in all_nodes:
              self.graph.add_node(node.id, **node.attributes)

          # 4. Create edges
          all_edges = self._create_all_edges(all_nodes)

          # 5. Add edges to graph
          for edge in all_edges:
              self.graph.add_edge(
                  edge.source,
                  edge.target,
                  relation=edge.relation,
                  confidence=edge.confidence,
                  source=edge.source_type
              )

          return self.graph

      def export_graph(self, output_file: str):
          """Export graph to JSON"""
          graph_data = {
              "nodes": [
                  {"id": n, **self.graph.nodes[n]}
                  for n in self.graph.nodes
              ],
              "edges": [
                  {
                      "from": u,
                      "to": v,
                      **self.graph.edges[u, v]
                  }
                  for u, v in self.graph.edges
              ],
              "statistics": {
                  "total_nodes": self.graph.number_of_nodes(),
                  "total_edges": self.graph.number_of_edges(),
                  "by_type": self._count_by_type()
              }
          }

          with open(output_file, 'w') as f:
              json.dump(graph_data, f, indent=2)
  ```

- [ ] **Output Files**:
  - `output/graph/code_based_graph.json` - Complete graph
  - `output/graph/low_confidence_edges.json` - Edges needing LLM verification (confidence < 0.8)
  - `output/graph/graph_statistics.json` - Statistics

#### 5.1.5: Validation & Quality Checks
- [ ] **Graph Validation**:
  - No orphan nodes (except intentional singletons)
  - No self-loops (unless intentional)
  - Edge direction consistency
  - Confidence values in valid range [0.0, 1.0]

- [ ] **Quality Metrics**:
  ```python
  {
    "coverage": {
      "jsp_with_controllers": 0.85,  # % JSPs with controller connections
      "controllers_with_services": 0.95,
      "services_with_mappers": 0.90,
      "mappers_with_sql": 1.0
    },
    "confidence_distribution": {
      "high (>= 0.9)": 1234,
      "medium (0.7-0.9)": 456,
      "low (< 0.7)": 89
    },
    "relationship_counts": {
      "INCLUDES": 234,
      "CALLS": 567,
      "INVOKES": 432,
      ...
    }
  }
  ```

**Deliverables**:
- ✅ `code_graph_builder.py` - Complete implementation
- ✅ `output/graph/code_based_graph.json` - Code-based graph
- ✅ `output/graph/low_confidence_edges.json` - Edges for LLM verification
- ✅ Unit tests for graph builder

---

### Phase 5.2: Graph Builder - Layer 2 (LLM-based) ⏳

**Goal**: Fill gaps and verify ambiguous relationships using LLM

**Duration**: 4-5 days

**Dependencies**: Phase 5.1 complete

#### 5.2.1: LLM Query Engine Setup
- [ ] **Semantic Cache Implementation** (`mcp_server/tools/semantic_cache.py`):
  ```python
  class SemanticCache:
      def __init__(self, cache_dir: str = ".llm_cache"):
          self.cache_dir = Path(cache_dir)
          self.cache_index = {}

      def semantic_hash(self, code: str, query_type: str) -> str:
          """Create semantic hash for caching"""
          # Normalize code (remove whitespace, comments)
          normalized = self._normalize_code(code)
          # Hash: normalized_code + query_type
          return hashlib.md5(f"{normalized}:{query_type}".encode()).hexdigest()

      def get(self, code: str, query_type: str) -> Optional[Dict]:
          """Get cached LLM result"""

      def set(self, code: str, query_type: str, result: Dict):
          """Cache LLM result"""

      def stats(self) -> Dict:
          """Get cache statistics"""
          return {
              "total_entries": len(self.cache_index),
              "hit_rate": self.hits / (self.hits + self.misses),
              "cost_saved": self.calculate_cost_saved()
          }
  ```

- [ ] **LLM Query Wrapper** (`mcp_server/tools/llm_query_engine.py`):
  ```python
  class LLMQueryEngine:
      def __init__(self):
          self.cache = SemanticCache()
          self.client = anthropic.Anthropic()

      async def verify_relationship(
          self,
          source_code: str,
          target_code: str,
          relationship_type: str,
          context: Dict
      ) -> Dict:
          """Verify a relationship using LLM"""

          # Check cache first
          cache_key = f"{source_code}:{target_code}:{relationship_type}"
          cached = self.cache.get(cache_key, "verify_relationship")
          if cached:
              return cached

          # Build XML-structured prompt
          prompt = self._build_verification_prompt(
              source_code, target_code, relationship_type, context
          )

          # Query LLM
          result = await self._query_llm(prompt)

          # Cache result
          self.cache.set(cache_key, "verify_relationship", result)

          return result

      def _build_verification_prompt(self, ...) -> str:
          """Build XML-structured prompt (15-20% accuracy boost)"""
          return f"""
          <task>Verify if {relationship_type} relationship exists</task>
          <context>
            <source>
              <type>{source_type}</type>
              <code>{source_code[:500]}</code>  <!-- ±15 lines sweet spot -->
            </source>
            <target>
              <type>{target_type}</type>
              <code>{target_code[:500]}</code>
            </target>
            <project_context>
              {json.dumps(context, indent=2)}
            </project_context>
          </context>
          <requirements>
            - Output JSON format
            - Include confidence (0.0-1.0)
            - Provide step-by-step reasoning
            - Consider edge cases
          </requirements>
          <examples>
            {self._get_few_shot_examples(relationship_type)}
          </examples>
          """
  ```

#### 5.2.2: Gap Filling - JSP to Controller Matching
- [ ] **URL Pattern Matching** (`mcp_server/tools/url_matcher.py`):
  ```python
  class URLMatcher:
      def __init__(self, llm_engine: LLMQueryEngine):
          self.llm = llm_engine

      async def match_ajax_to_controller(
          self,
          ajax_call: Dict,  # From JSP analysis
          controllers: List[Dict]  # All controllers
      ) -> Dict:
          """Match AJAX URL to controller endpoint"""

          # Extract URL from AJAX call
          url = ajax_call['url']
          method = ajax_call['method']  # GET/POST

          # Find candidate controllers by URL pattern
          candidates = self._find_candidate_controllers(url, method, controllers)

          if len(candidates) == 1:
              return {"target": candidates[0], "confidence": 0.9, "method": "pattern_match"}

          if len(candidates) == 0:
              return {"target": None, "confidence": 0.0, "method": "no_match"}

          # Multiple candidates - use LLM to disambiguate
          context = {
              "ajax_call": ajax_call,
              "candidates": candidates
          }

          result = await self.llm.verify_relationship(
              source_code=ajax_call['code_snippet'],
              target_code=json.dumps(candidates, indent=2),
              relationship_type="AJAX_TO_CONTROLLER",
              context=context
          )

          return result

      def _find_candidate_controllers(self, url: str, method: str,
                                        controllers: List[Dict]) -> List[Dict]:
          """Find controllers matching URL pattern"""
          candidates = []

          for controller in controllers:
              for endpoint in controller['endpoints']:
                  if self._url_matches(url, endpoint['path']) and \
                     method.upper() in endpoint['method']:
                      candidates.append({
                          "controller": controller['class_name'],
                          "method": endpoint['handler'],
                          "path": endpoint['path']
                      })

          return candidates

      def _url_matches(self, ajax_url: str, mapping_path: str) -> bool:
          """Check if AJAX URL matches @RequestMapping path"""
          # Handle EL expressions: ${ctx}/user/list -> /user/list
          # Handle path variables: /user/{id} matches /user/123
          # Handle wildcards: /user/* matches /user/anything
  ```

#### 5.2.3: Completeness Scanning
- [ ] **Orphan Detection**:
  ```python
  class CompletenessScanner:
      async def find_orphan_nodes(self, graph: nx.DiGraph) -> List[str]:
          """Find nodes with no incoming or outgoing edges"""

      async def find_missing_relationships(self, graph: nx.DiGraph) -> List[Dict]:
          """Find likely missing relationships using LLM"""
          # Example: Controller with no Service calls (suspicious)
          # Example: Service with no Mapper usage (suspicious)

      async def verify_suspicious_patterns(self, graph: nx.DiGraph) -> List[Dict]:
          """Use LLM to verify suspicious patterns"""
  ```

- [ ] **LLM Verification Queries**:
  ```python
  VERIFICATION_QUERIES = {
      "orphan_controller": "This controller has no service calls. Is this intentional?",
      "orphan_service": "This service has no mapper usage. Does it call external APIs?",
      "missing_ajax": "This JSP has forms but no AJAX. Are there missing endpoints?",
      "unused_mapper": "This mapper is not called by any service. Is it legacy code?"
  }
  ```

#### 5.2.4: Prompt Engineering Best Practices
- [ ] **Context Window Optimization**:
  - ±15 lines of code (sweet spot from research)
  - Include surrounding context for better understanding

- [ ] **Few-Shot Examples**:
  ```python
  FEW_SHOT_EXAMPLES = {
      "AJAX_TO_CONTROLLER": [
          {
              "positive": {
                  "ajax": "$.post('${ctx}/user/save', data)",
                  "controller": "@PostMapping('/user/save')",
                  "match": True,
                  "confidence": 0.95
              }
          },
          {
              "negative": {
                  "ajax": "$.get('/api/users')",
                  "controller": "@GetMapping('/user/list')",
                  "match": False,
                  "confidence": 0.0
              }
          },
          {
              "edge_case": {
                  "ajax": "$.post('/user/' + id + '/update')",
                  "controller": "@PostMapping('/user/{id}/update')",
                  "match": True,
                  "confidence": 0.85,
                  "reasoning": "Path variable {id} matches dynamic URL construction"
              }
          }
      ]
  }
  ```

- [ ] **Step-by-Step Reasoning** (15-20% accuracy boost):
  ```xml
  <thinking>
    1. Extract URL pattern from AJAX call
    2. Normalize URL (remove context path, handle variables)
    3. Compare with controller mappings
    4. Check HTTP method match
    5. Consider path variables and wildcards
    6. Assign confidence based on match quality
  </thinking>
  <conclusion>
    {
      "match": true,
      "confidence": 0.9,
      "reasoning": "URL pattern and HTTP method match exactly"
    }
  </conclusion>
  ```

**Deliverables**:
- ✅ `llm_query_engine.py` - LLM query wrapper with caching
- ✅ `url_matcher.py` - AJAX to Controller matching
- ✅ `completeness_scanner.py` - Orphan detection and gap filling
- ✅ `output/graph/llm_verified_edges.json` - LLM-verified relationships
- ✅ Cache statistics report (hit rate, cost saved)

---

### Phase 5.3: Graph Merger ⏳

**Goal**: Merge code-based and LLM-verified graphs with conflict resolution

**Duration**: 2-3 days

**Dependencies**: Phase 5.1 & 5.2 complete

#### 5.3.1: Conflict Resolution
- [ ] **Conflict Detection** (`mcp_server/tools/graph_merger.py`):
  ```python
  class GraphMerger:
      def detect_conflicts(
          self,
          code_graph: nx.DiGraph,
          llm_graph: nx.DiGraph
      ) -> List[Conflict]:
          """Detect conflicts between graphs"""
          conflicts = []

          # Type 1: Different relationships for same node pair
          for u, v in code_graph.edges:
              if (u, v) in llm_graph.edges:
                  code_rel = code_graph.edges[u, v]['relation']
                  llm_rel = llm_graph.edges[u, v]['relation']
                  if code_rel != llm_rel:
                      conflicts.append({
                          "type": "RELATION_MISMATCH",
                          "nodes": (u, v),
                          "code_relation": code_rel,
                          "llm_relation": llm_rel
                      })

          # Type 2: Contradictory relationships
          # e.g., code says A->B, LLM says B->A

          return conflicts
  ```

- [ ] **Resolution Rules**:
  ```python
  RESOLUTION_RULES = {
      "RELATION_MISMATCH": {
          "priority": "code",  # Code-based always wins
          "action": "keep_code_relation",
          "log": "warn"
      },
      "CONFIDENCE_CONFLICT": {
          "priority": "highest_confidence",
          "action": "compare_confidence",
          "threshold": 0.8
      },
      "DIRECTION_CONFLICT": {
          "priority": "code",
          "action": "keep_code_direction",
          "log": "error"  # This is serious
      }
  }
  ```

#### 5.3.2: Confidence Scoring
- [ ] **Combined Confidence**:
  ```python
  def calculate_combined_confidence(
      code_edge: Optional[Dict],
      llm_edge: Optional[Dict]
  ) -> float:
      """Calculate combined confidence score"""

      if code_edge and llm_edge:
          # Both agree - boost confidence
          base_conf = max(code_edge['confidence'], llm_edge['confidence'])
          agreement_bonus = 0.1
          return min(1.0, base_conf + agreement_bonus)

      elif code_edge:
          # Only code - use as-is
          return code_edge['confidence']

      elif llm_edge:
          # Only LLM - penalty for no code evidence
          return llm_edge['confidence'] * 0.9

      else:
          return 0.0
  ```

#### 5.3.3: Merge Algorithm
- [ ] **Merge Implementation**:
  ```python
  def merge_graphs(
      self,
      code_graph: nx.DiGraph,
      llm_graph: nx.DiGraph
  ) -> nx.DiGraph:
      """Merge code and LLM graphs"""
      merged = nx.DiGraph()

      # Step 1: Add all nodes (union)
      all_nodes = set(code_graph.nodes) | set(llm_graph.nodes)
      for node in all_nodes:
          attrs = code_graph.nodes.get(node, llm_graph.nodes.get(node))
          merged.add_node(node, **attrs)

      # Step 2: Merge edges with conflict resolution
      all_edges = set(code_graph.edges) | set(llm_graph.edges)
      for u, v in all_edges:
          code_edge = code_graph.edges.get((u, v))
          llm_edge = llm_graph.edges.get((u, v))

          # Detect conflict
          if code_edge and llm_edge:
              if code_edge['relation'] != llm_edge['relation']:
                  # Conflict - apply resolution rules
                  edge_data = self._resolve_conflict(code_edge, llm_edge)
              else:
                  # Agreement - combine confidence
                  edge_data = code_edge.copy()
                  edge_data['confidence'] = self.calculate_combined_confidence(
                      code_edge, llm_edge
                  )
                  edge_data['verified_by'] = 'code+llm'
          elif code_edge:
              edge_data = code_edge.copy()
              edge_data['verified_by'] = 'code'
          else:
              edge_data = llm_edge.copy()
              edge_data['verified_by'] = 'llm'

          merged.add_edge(u, v, **edge_data)

      return merged
  ```

**Deliverables**:
- ✅ `graph_merger.py` - Complete merger implementation
- ✅ `output/graph/merged_graph.json` - Final merged graph
- ✅ `output/graph/conflicts.json` - Detected conflicts and resolutions
- ✅ Merge statistics and quality report

---

### Phase 5.4: Visualization ⏳

**Goal**: Create interactive and exportable visualizations

**Duration**: 2-3 days

**Dependencies**: Phase 5.3 complete

#### 5.4.1: PyVis Interactive HTML
- [ ] **PyVis Implementation** (`mcp_server/tools/graph_visualizer.py`):
  ```python
  from pyvis.network import Network

  class GraphVisualizer:
      def create_interactive_html(
          self,
          graph: nx.DiGraph,
          output_file: str = "output/graph/interactive_graph.html"
      ):
          """Create interactive PyVis HTML visualization"""

          net = Network(
              height="800px",
              width="100%",
              directed=True,
              notebook=False,
              cdn_resources='in_line'
          )

          # Configure physics
          net.set_options("""
          {
            "physics": {
              "enabled": true,
              "solver": "forceAtlas2Based",
              "forceAtlas2Based": {
                "gravitationalConstant": -50,
                "centralGravity": 0.01,
                "springLength": 100
              }
            },
            "nodes": {
              "font": {"size": 14}
            },
            "edges": {
              "arrows": {"to": {"enabled": true}},
              "smooth": {"type": "continuous"}
            }
          }
          """)

          # Add nodes with colors and shapes from NODE_TYPES
          for node_id, attrs in graph.nodes(data=True):
              node_type = attrs['type']
              config = NODE_TYPES[node_type]

              net.add_node(
                  node_id,
                  label=attrs.get('display_name', node_id),
                  title=self._create_tooltip(node_id, attrs),
                  color=config['color'],
                  shape=config['shape'],
                  size=self._calculate_node_size(node_id, graph)
              )

          # Add edges with confidence-based styling
          for u, v, attrs in graph.edges(data=True):
              confidence = attrs.get('confidence', 0.5)

              net.add_edge(
                  u, v,
                  title=f"{attrs['relation']} (conf: {confidence:.2f})",
                  color=self._get_edge_color(confidence),
                  width=confidence * 3,
                  label=attrs['relation']
              )

          # Save
          net.save_graph(output_file)

      def _create_tooltip(self, node_id: str, attrs: Dict) -> str:
          """Create HTML tooltip for node"""
          html = f"<b>{node_id}</b><br>"
          html += f"Type: {attrs['type']}<br>"
          if 'path' in attrs:
              html += f"Path: {attrs['path']}<br>"
          if 'confidence' in attrs:
              html += f"Confidence: {attrs['confidence']:.2f}<br>"
          return html

      def _get_edge_color(self, confidence: float) -> str:
          """Color edges by confidence"""
          if confidence >= 0.9:
              return "#27AE60"  # Green - high confidence
          elif confidence >= 0.7:
              return "#F39C12"  # Orange - medium confidence
          else:
              return "#E74C3C"  # Red - low confidence
  ```

#### 5.4.2: Mermaid Diagrams
- [ ] **Mermaid Generator** (`mcp_server/tools/mermaid_generator.py`):
  ```python
  class MermaidGenerator:
      def generate_mermaid(
          self,
          graph: nx.DiGraph,
          max_nodes: int = 50
      ) -> str:
          """Generate Mermaid diagram (for smaller subgraphs)"""

          # Select most important nodes if too large
          if graph.number_of_nodes() > max_nodes:
              important_nodes = self._select_important_nodes(graph, max_nodes)
              subgraph = graph.subgraph(important_nodes)
          else:
              subgraph = graph

          mermaid = "graph TD\n"

          # Add nodes
          for node_id, attrs in subgraph.nodes(data=True):
              node_type = attrs['type']
              display = attrs.get('display_name', node_id).replace('"', "'")
              mermaid += f'  {self._sanitize_id(node_id)}["{display}"]\n'

          # Add edges
          for u, v, attrs in subgraph.edges(data=True):
              relation = attrs['relation']
              mermaid += f'  {self._sanitize_id(u)} -->|{relation}| {self._sanitize_id(v)}\n'

          return mermaid

      def save_mermaid_file(self, mermaid_code: str, output_file: str):
          """Save Mermaid diagram to markdown file"""
          with open(output_file, 'w') as f:
              f.write("```mermaid\n")
              f.write(mermaid_code)
              f.write("\n```\n")
  ```

#### 5.4.3: GraphML Export (for Gephi)
- [ ] **GraphML Export**:
  ```python
  def export_to_graphml(
      self,
      graph: nx.DiGraph,
      output_file: str = "output/graph/graph.graphml"
  ):
      """Export to GraphML for Gephi analysis"""
      nx.write_graphml(graph, output_file)
  ```

#### 5.4.4: Subgraph Extraction
- [ ] **Subgraph Tools**:
  ```python
  class SubgraphExtractor:
      def extract_path_subgraph(
          self,
          graph: nx.DiGraph,
          start_node: str,
          end_node: str
      ) -> nx.DiGraph:
          """Extract subgraph containing all paths from start to end"""

      def extract_component_subgraph(
          self,
          graph: nx.DiGraph,
          node_id: str,
          max_hops: int = 2
      ) -> nx.DiGraph:
          """Extract subgraph within N hops of a node"""

      def extract_layer_subgraph(
          self,
          graph: nx.DiGraph,
          layer: str  # "controller", "service", "mapper"
      ) -> nx.DiGraph:
          """Extract subgraph of specific layer"""
  ```

**Deliverables**:
- ✅ `graph_visualizer.py` - PyVis HTML generator
- ✅ `mermaid_generator.py` - Mermaid diagram generator
- ✅ `output/graph/interactive_graph.html` - Interactive visualization
- ✅ `output/graph/overview.mermaid.md` - Mermaid diagram
- ✅ `output/graph/graph.graphml` - Gephi export
- ✅ Subgraph extraction utilities

---

## Success Criteria

### Phase 5.1 (Code-based Graph)
- [ ] ✅ All Phase 3 analysis results loaded successfully
- [ ] ✅ Graph contains > 90% of expected nodes
- [ ] ✅ High-confidence edges (>= 0.9) represent > 70% of total edges
- [ ] ✅ No critical errors in graph construction
- [ ] ✅ Graph statistics report generated

### Phase 5.2 (LLM-based Graph)
- [ ] ✅ Semantic cache hit rate >= 60%
- [ ] ✅ LLM verification cost < $50 for medium project
- [ ] ✅ Ambiguous relationships resolved with confidence scores
- [ ] ✅ Orphan nodes reduced by >= 50%
- [ ] ✅ Gap filling identifies >= 80% of missing relationships

### Phase 5.3 (Merged Graph)
- [ ] ✅ Conflicts detected and resolved
- [ ] ✅ Merged graph contains all nodes from both layers
- [ ] ✅ No unresolved conflicts
- [ ] ✅ Confidence scores calculated for all edges
- [ ] ✅ Quality report shows improvement over code-only graph

### Phase 5.4 (Visualization)
- [ ] ✅ Interactive HTML loads and is navigable
- [ ] ✅ Node colors/shapes represent types correctly
- [ ] ✅ Edge confidence visually distinguishable
- [ ] ✅ Mermaid diagrams render correctly
- [ ] ✅ GraphML imports into Gephi successfully

---

## Risk Mitigation

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Graph too large for visualization | High | Medium | Implement filtering, layering, subgraph extraction |
| LLM costs exceed budget | Medium | High | Aggressive caching, use Haiku for screening |
| URL matching accuracy low | Medium | Medium | Combine pattern matching + LLM verification |
| Conflicting relationships | Low | Medium | Clear resolution rules, code priority |
| Performance issues with large graphs | Medium | Medium | Use sparse matrix, optimize NetworkX operations |

### Process Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Phase 3 analysis incomplete | Low | High | Validate inputs, handle missing data gracefully |
| LLM prompt engineering iterations | High | Medium | Start with proven patterns from research |
| Visualization complexity | Medium | Low | Start with basic, iterate based on feedback |

---

## Testing Strategy

### Unit Tests
- [ ] Node builder tests (all 11 node types)
- [ ] Edge builder tests (all edge types)
- [ ] Confidence calculation tests
- [ ] Semantic cache tests
- [ ] Conflict resolution tests

### Integration Tests
- [ ] End-to-end graph building (sample project)
- [ ] LLM verification (mocked responses)
- [ ] Merge algorithm (synthetic conflicts)
- [ ] Visualization generation

### Performance Tests
- [ ] Graph building with 1000+ nodes
- [ ] LLM query batching efficiency
- [ ] Cache hit rate measurement
- [ ] Visualization rendering time

---

## Dependencies

### External Libraries
```python
# requirements.txt additions
networkx>=3.0
pyvis>=0.3.2
python-louvain>=0.16  # For community detection
```

### Phase 3 Prerequisites
- All analyzers must output standardized JSON
- Analysis results must be cached and accessible
- DB schema extraction complete

---

## Timeline

### Week 1
- Day 1-2: Phase 5.1.1-5.1.2 (Data loading + Node creation)
- Day 3-4: Phase 5.1.3-5.1.4 (Edge creation + Graph construction)
- Day 5: Phase 5.1.5 (Validation + Testing)

### Week 2
- Day 1-2: Phase 5.2.1-5.2.2 (LLM setup + URL matching)
- Day 3-4: Phase 5.2.3-5.2.4 (Completeness scanning)
- Day 5: Phase 5.2 testing and optimization

### Week 3
- Day 1-2: Phase 5.3 (Graph merging)
- Day 3-4: Phase 5.4 (Visualization)
- Day 5: Final testing, documentation, delivery

---

## Deliverables Summary

### Code
- [ ] `graph_data_loader.py` - Load all Phase 3 results
- [ ] `graph_node_builder.py` - Create 11 node types
- [ ] `graph_edge_builder.py` - Create typed edges
- [ ] `code_graph_builder.py` - Code-based graph builder
- [ ] `semantic_cache.py` - LLM response caching
- [ ] `llm_query_engine.py` - LLM query wrapper
- [ ] `url_matcher.py` - AJAX to Controller matching
- [ ] `completeness_scanner.py` - Gap detection
- [ ] `graph_merger.py` - Merge algorithm
- [ ] `graph_visualizer.py` - PyVis HTML generator
- [ ] `mermaid_generator.py` - Mermaid diagrams
- [ ] `subgraph_extractor.py` - Subgraph tools

### Data
- [ ] `output/graph/code_based_graph.json`
- [ ] `output/graph/llm_verified_edges.json`
- [ ] `output/graph/merged_graph.json`
- [ ] `output/graph/conflicts.json`
- [ ] `output/graph/graph_statistics.json`

### Visualizations
- [ ] `output/graph/interactive_graph.html` (PyVis)
- [ ] `output/graph/overview.mermaid.md` (Mermaid)
- [ ] `output/graph/graph.graphml` (Gephi)

### Documentation
- [ ] Phase 5 completion report
- [ ] Visualization user guide
- [ ] Graph schema documentation
- [ ] LLM prompt library

---

## Next Steps After Phase 5

With complete knowledge graph:
1. **Phase 6**: Testing & Documentation
2. **Phase 7**: Semantic Enhancement (business logic analysis)
3. **Production**: Deploy as service/tool

---

**Status**: Planning Complete - Ready for Review
**Last Updated**: 2025-10-05
