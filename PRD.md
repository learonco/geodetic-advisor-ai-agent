# **SPECIFICATION: Geodetic AI-visor Project**

## **1. PROJECT OVERVIEW**

### **1.1 Project Name**
Geodetic AI-visor

### **1.2 Purpose**
An intelligent AI-powered advisory system that leverages Large Language Models (LLMs) and specialized geodetic tools to assist users in:
- Selecting appropriate geodetic reference frames for specific geographic areas and use cases
- Designing optimal map projections based on area of interest and project requirements
- Searching and retrieving coordinate reference systems (CRS) from the EPSG geodetic parameter registry
- Performing coordinate transformations between reference frames
- Understanding geodetic metadata and specifications

### **1.3 Vision**
Democratize access to complex geodetic and geospatial knowledge by providing an intelligent conversational interface that eliminates the need for deep expertise in coordinate reference systems and geodetic mathematics.

---

## **2. PROJECT OBJECTIVES**

### **2.1 Primary Objectives**
1. **Intelligent CRS Recommendation**: Enable users to discover appropriate CRS/geodetic systems by describing their geographic area or use case in natural language
2. **Geodetic Knowledge Assistant**: Provide authoritative information about geodetic reference frames, datums, transformations, and projections
3. **Operational Efficiency**: Reduce time required to research and implement correct geodetic specifications in geospatial projects
4. **EPSG Registry Integration**: Seamless querying of the EPSG geodetic parameter database with intelligent filtering

### **2.2 Secondary Objectives**
1. Support multi-language queries through LLM translation capabilities
2. Maintain accuracy and compliance with international geodetic standards
3. Provide transparent reasoning for geodetic recommendations
4. Enable educational use cases for learning geodetic concepts

---

## **3. FEATURE SPECIFICATION**

### **3.1 Core Features**

#### **3.1.1 CRS Search and Discovery**
- **Input Methods**:
  - Geographic area name (e.g., "Argentina", "Tokyo Bay")
  - Bounding box coordinates (west, south, east, north)
  - Geodetic object name or partial name
  - EPSG code (numeric or EPSG:xxxx format)
  - Area of use keywords

- **Search Filtering**:
  - By object type (Geodetic Reference Frame, Projected CRS, Geographic CRS, Vertical CRS, Compound CRS, etc.)
  - By area of interest with spatial filtering
  - By area of use text matching
  - Exclude deprecated systems
  - Multiple filter combination support

- **Output Information**:
  - CRS name and EPSG code
  - Datum information
  - Projection type and parameters
  - Area of use and spatial extent
  - Coordinate system type
  - Accuracy/uncertainty information

#### **3.1.2 Coordinate Transformation**
- **Capabilities**:
  - Transform coordinates between any two EPSG CRS codes
  - Support for geographic, projected, and vertical coordinates
  - Batch transformation support (future)
  - Distance and bearing calculations (future)

- **Input Format**: `x,y,from_epsg,to_epsg` (with flexible parsing)

- **Output**:
  - Transformed coordinates with appropriate precision
  - Transformation method used
  - Estimated transformation accuracy (future)

#### **3.1.3 Geodetic Reference Frame Selection**
- **Selection Criteria**:
  - Geographic location/area of interest
  - Accuracy requirements
  - Project type (cartography, surveying, engineering, etc.)
  - Regional vs. global scope
  - Historical vs. modern considerations

- **Recommendation Logic**:
  - Query EPSG database for area
  - Filter by object type (reference frames)
  - Rank by relevance and area coverage
  - Present alternatives with trade-offs

#### **3.1.4 Map Projection Design Assistance**
- **Analysis Factors**:
  - Area of interest characteristics (size, shape, location)
  - Distortion tolerance (area, angle, distance)
  - Intended use case (thematic mapping, navigation, etc.)
  - Scale requirements
  - Reference frame compatibility

- **Recommendation Approach** (future iteration):
  - Suggest commonly used projections for the area
  - Explain distortion characteristics
  - Compare alternative projections
  - Provide implementation guidance

#### **3.1.5 Interactive Geodetic Query System**
- **Natural Language Processing**:
  - Parse user questions about geodetic topics
  - Extract intent (lookup, transformation, search, design)
  - Extract entities (area names, EPSG codes, coordinate values)
  - Handle ambiguous queries with clarifications

- **Conversational Context**:
  - Maintain context across multiple queries
  - Reference previous results in follow-up questions
  - Support iterative refinement of queries

---

## **4. TECHNICAL SPECIFICATION**

### **4.1 Architecture Overview**

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                      │
│          (CLI, Web UI, Chat Interface - Future)              │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                  LangChain Agent Layer                       │
│         (Query Routing & Decision Making)                    │
│  - System Prompt: Geodetic Knowledge Base                    │
│  - Tool Invocation Logic                                     │
└────────────────────┬────────────────────────────────────────┘
                     │
          ┌──────────┼──────────┐
          │          │          │
    ┌─────▼──┐  ┌───▼────┐  ┌─▼──────┐
    │  Tools │  │ Tools  │  │ Tools  │
    │ Layer  │  │ Layer  │  │ Layer  │
    └────────┘  └────────┘  └────────┘
          │          │          │
   ┌──────▼──────────▼──────────▼──────┐
   │      External Data Sources         │
   ├─────────────────────────────────────┤
   │ • EPSG Database (pyproj)            │
   │ • Nominatim/OSM API                 │
   │ • Geospatial Calculation Engine     │
   └─────────────────────────────────────┘
```

### **4.2 Current Technology Stack**

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| LLM | Google Gemini 2.5-Flash | Latest | Natural language understanding & generation |
| Agent Framework | LangChain | ≥1.1.0 | Tool orchestration & prompt management |
| Geodetic Engine | pyproj | ≥3.7.2 | CRS database & coordinate transformations |
| HTTP Client | httpx | Latest | External API calls (Nominatim) |
| Language | Python | ≥3.13 | Implementation language |
| Package Manager | pip/Poetry | Latest | Dependency management |

### **4.3 Core Tools Layer**

#### **Tool 1: `search_crs_objects`**
**Purpose**: Query EPSG database for applicable CRS objects
**Parameters**:
- `bbox`: dict (west, south, east, north)
- `object_type`: PJType | list[PJType]
- `object_name`: str (filter by name)
- `object_area_of_use`: str (text search)

**Returns**: list[CRSInfo]

**Implementation**: pyproj `database.query_crs_info()`

#### **Tool 2: `get_bbox_from_areaname`**
**Purpose**: Convert geographic area names to bounding box coordinates
**Parameters**:
- `area_name`: str (e.g., "Argentina", "Tokyo")

**Returns**: dict {west, south, east, north}

**Implementation**: Nominatim OpenStreetMap API via httpx

#### **Tool 3: `transform_coordinates`**
**Purpose**: Transform point coordinates between two EPSG CRS codes
**Parameters**:
- `query`: str (format: "x,y,from_epsg,to_epsg")

**Returns**: str (transformed coordinates)

**Implementation**: pyproj `Transformer.from_crs()`

#### **Tool 4: `lookup_crs`**
**Purpose**: Retrieve metadata for a specific EPSG code
**Parameters**:
- `epsg_code`: str (e.g., "4326")

**Returns**: str (formatted metadata)

**Implementation**: pyproj `CRS.from_epsg()`

### **4.4 Agent Configuration**

**Current Agent**: `geodetic_agent` in `agents/geodetic.py`
- **LLM**: Google Gemini 2.5-Flash (temperature=0 for consistency)
- **Tool Set**: All four core tools
- **System Prompt**: Geodetic domain-specific instructions with use-case examples
- **Execution Mode**: ReAct (Reasoning + Acting)

---

## **5. CONSTRAINTS & LIMITATIONS**

### **5.1 Technical Constraints**

| Constraint | Details | Impact |
|-----------|---------|--------|
| **EPSG Database Currency** | Depends on pyproj version | May lag behind EPSG registry by version updates |
| **API Rate Limits** | Nominatim has usage policies | Rate limiting for area lookups may apply |
| **LLM Context Window** | Gemini 2.5-Flash limitations | Affects max result sizes returned |
| **Coordinate Precision** | Float precision (±6-8 decimal places) | Suitable for most use cases; limitations for RTK |
| **Python Version** | Requires Python 3.13+ | Not compatible with older Python versions |
| **Network Dependency** | Relies on external APIs | Nominatim API availability affects functionality |

### **5.2 Functional Limitations (Current Release)**

| Limitation | Scope | Notes |
|-----------|-------|-------|
| **Single Point Transformation** | Only supports point-to-point transformations | Batch processing not implemented |
| **No Vertical Datum Handling** | Limited support for vertical reference frames | Horizontal-only focus |
| **No Grid-Based Transforms** | Uses analytical transformations only | High-precision grid-based methods not available |
| **Limited Projection Design** | Suggests existing CRS; doesn't create new projections | Custom projection parameters not generated |
| **No Multi-Language Output** | All outputs in English | Translation of results not implemented |
| **Single LLM Provider** | Only Google Gemini integration | No LLM provider abstraction |

### **5.3 Data Constraints**

- EPSG database accuracy depends on upstream data quality
- Nominatim geographic boundaries are approximate
- Coordinate transformations have inherent mathematical uncertainties
- Deprecated CRS are excluded from searches by design

### **5.4 Operational Constraints**

- **API Credentials**: Requires valid `GEMINI_API_KEY` environment variable
- **Internet Connectivity**: Required for Nominatim API and Gemini inference
- **Service Availability**: Dependent on Google Cloud and OpenStreetMap infrastructure
- **Usage Volume**: No built-in rate limiting or queue management

---

## **6. IMPLEMENTATION ROADMAP**

### **Phase 1: Foundation (Current - Complete)**
**Timeline**: Q1 2026
**Objectives**: Establish core functionality and validate approach

**Deliverables**:
- ✅ LangChain agent setup with Gemini integration
- ✅ Core tool implementations (4 tools)
- ✅ EPSG database querying capability
- ✅ Coordinate transformation pipeline
- ✅ Area name to bounding box resolution
- ✅ Basic system prompt and tool descriptions
- ✅ Initial test suite

**Current Status**: Core functionality operational

---

### **Phase 2: Enhancement & Polish (Planned - Q2 2026)**
**Timeline**: Q2 2026
**Objectives**: Improve UX, expand capabilities, add robustness

**Features to Implement**:
1. **Enhanced Error Handling**
   - Graceful handling of API failures
   - User-friendly error messages
   - Retry logic with exponential backoff
   - Detailed logging system

2. **Expanded Tool Set**
   - `analyze_projection_distortion`: Analyze distortion characteristics
   - `get_datum_details`: Detailed datum information
   - `batch_transform_coordinates`: Multiple point transformation
   - `recommend_projection`: Intelligent projection recommendation engine
   - `get_coordinate_system_info`: Detailed CS information

3. **Testing Infrastructure**
   - Unit tests for all tools
   - Integration tests for agent behavior
   - Mock API responses for testing
   - Test coverage reporting
   - CI/CD pipeline setup

4. **Documentation**
   - API documentation
   - Tool usage examples
   - System architecture diagram
   - Configuration guide
   - Troubleshooting guide

5. **Performance Optimization**
   - Response caching (with TTL)
   - EPSG database indexing
   - Lazy loading of large result sets
   - Request batching

**Deliverables**:
- Complete test suite (>80% coverage)
- Expanded tool library (7+ tools)
- Comprehensive documentation
- Performance benchmarks
- GitHub Actions CI/CD workflow

---

### **Phase 3: User Interface Layer (Planned - Q3 2026)**
**Timeline**: Q3 2026
**Objectives**: Make system accessible to non-technical users

**Components**:
1. **CLI Interface** (Priority 1)
   - Command-line argument parsing
   - Interactive REPL mode
   - Output formatting (JSON, table, text)
   - Configuration file support

2. **Web UI** (Priority 2)
   - FastAPI backend
   - Frontend (React/Vue)
   - Chat interface
   - Result visualization
   - Map preview integration

3. **API Gateway**
   - REST API endpoints
   - Request validation
   - Response formatting
   - Authentication/authorization (optional)

**Deliverables**:
- Functional CLI with help system
- Web UI with responsive design
- REST API documentation (OpenAPI/Swagger)
- Docker containerization
- Deployment guide

---

### **Phase 4: Advanced Features (Planned - Q4 2026)**
**Timeline**: Q4 2026
**Objectives**: Add sophisticated geodetic capabilities

**Features**:
1. **Projection Design Engine**
   - Custom projection parameter generation
   - Mathematical distortion analysis
   - Regional optimization algorithms
   - Multi-criteria selection (area vs. angle vs. distance)

2. **Multi-Provider LLM Support**
   - Abstract LLM interface
   - Support for OpenAI, Anthropic, Local models
   - Provider-specific optimization

3. **Historical CRS Support**
   - Search deprecated CRS with warnings
   - Historical datum transformations
   - Legacy coordinate system support

4. **Advanced Transformations**
   - Grid-based transformations (NTv2, etc.)
   - Vertical datum transformations
   - Time-dependent transformations
   - High-precision RTK workflows

5. **Data Export & Integration**
   - Export CRS definitions (PRJ, WKT, JSON)
   - Integration with GIS software (QGIS, ArcGIS)
   - Coordinate transformation pipelines
   - Spatial reference system databases

**Deliverables**:
- Production-grade projection engine
- Multi-provider LLM abstraction layer
- Advanced transformation capabilities
- GIS software integration modules
- Performance documentation

---

### **Phase 5: Enterprise & Scaling (Planned - 2027+)**
**Timeline**: 2027 onwards
**Objectives**: Prepare for production deployment and scaling

**Features**:
1. **Enterprise Features**
   - Multi-user authentication
   - Usage analytics & reporting
   - Audit logging
   - Custom organization workspaces
   - Role-based access control

2. **Scalability**
   - Load balancing
   - Caching layer (Redis)
   - Database integration (PostgreSQL for results)
   - Microservices architecture options
   - Kubernetes deployment configs

3. **Knowledge Management**
   - Fine-tuned LLM models
   - Custom knowledge base
   - User feedback integration
   - Best practices repository

4. **Quality Assurance**
   - Automated testing at scale
   - Performance monitoring
   - Error tracking (Sentry)
   - Uptime monitoring

---

## **7. STEP-BY-STEP DEVELOPMENT PLAN**

### **Immediate Next Steps (Week 1-2)**

**Step 1: Code Organization & Architecture**
- [ ] Restructure project with clear module organization
- [ ] Create `config/` directory for configuration management
- [ ] Create `models/` directory for data classes/schemas
- [ ] Create `services/` directory for business logic services
- [ ] Document module responsibilities

**Step 2: Error Handling & Robustness**
- [ ] Add comprehensive error handling to all tools
- [ ] Create custom exception classes
- [ ] Add input validation to all tool functions
- [ ] Add logging throughout the codebase
- [ ] Create error handling guidelines document

**Step 3: Configuration Management**
- [ ] Create `.env.example` with required variables
- [ ] Implement environment variable loading
- [ ] Add configuration validation on startup
- [ ] Support multiple environment configurations (dev, test, prod)

---

### **Short-term Plan (Week 3-8)**

**Step 4: Comprehensive Testing**
- [ ] Set up pytest framework with fixtures
- [ ] Create unit tests for all tools
- [ ] Create integration tests for agent behavior
- [ ] Add mock API responses for external services
- [ ] Achieve >80% code coverage
- [ ] Set up coverage reports in CI/CD

**Step 5: Documentation**
- [ ] Write API documentation for all tools
- [ ] Create architecture design documents
- [ ] Write configuration guide
- [ ] Create troubleshooting FAQ
- [ ] Add usage examples and tutorials

**Step 6: Performance Optimization**
- [ ] Implement result caching with TTL
- [ ] Profile tool execution times
- [ ] Optimize EPSG database queries
- [ ] Add performance benchmarks
- [ ] Document performance characteristics

**Step 7: Tool Expansion**
- [ ] Implement `analyze_projection_distortion` tool
- [ ] Implement `get_datum_details` tool
- [ ] Implement `recommend_projection` tool
- [ ] Add tool test coverage
- [ ] Update system prompt with new tools

---

### **Mid-term Plan (Week 9-16)**

**Step 8: CLI Development**
- [ ] Design CLI argument structure
- [ ] Implement command parser with Click/argparse
- [ ] Create interactive REPL mode
- [ ] Add output formatters (table, JSON, text)
- [ ] Add color/styling to output
- [ ] Document CLI usage

**Step 9: Web UI Foundation**
- [ ] Set up FastAPI application structure
- [ ] Create REST API endpoints for each tool
- [ ] Add request validation and documentation
- [ ] Create basic frontend skeleton (Vue/React)
- [ ] Implement chat interface component
- [ ] Deploy to development server

**Step 10: CI/CD Pipeline**
- [ ] Set up GitHub Actions workflows
- [ ] Configure automated testing
- [ ] Add code quality checks (flake8, black)
- [ ] Create deployment workflows
- [ ] Document CI/CD process

---

### **Long-term Plan (Week 17-32)**

**Step 11: Advanced Features**
- [ ] Implement projection design engine
- [ ] Add multi-provider LLM support
- [ ] Create batch transformation capability
- [ ] Add custom CRS creation tools
- [ ] Implement grid-based transformations

**Step 12: Production Readiness**
- [ ] Add monitoring and logging infrastructure
- [ ] Implement rate limiting
- [ ] Create backup/recovery procedures
- [ ] Write deployment documentation
- [ ] Conduct security audit

**Step 13: Scaling & Enterprise**
- [ ] Implement multi-user support
- [ ] Add authentication system
- [ ] Create usage analytics
- [ ] Set up database integration
- [ ] Document scalability patterns

---

## **8. SUCCESS CRITERIA & KPIs**

### **Functional Success Criteria**
- ✅ Agent correctly interprets 90%+ of geodetic queries
- ✅ CRS recommendations match expert recommendations
- ✅ All queries respond within 5 seconds (p95)
- ✅ Tool accuracy matches pyproj/EPSG database baseline
- ✅ No false-positive or dangerous recommendations

### **Quality Metrics**
- Code coverage: >80%
- Test pass rate: 100%
- Documentation completeness: >90%
- Code quality score: A/B grade (linting)

### **Performance Metrics**
- Average response time: <2 seconds
- P95 response time: <5 seconds
- API availability: >99.5%
- Tool error rate: <1%

### **User Adoption Metrics** (Phase 3+)
- User engagement rate
- Query complexity trends
- Feature utilization rates
- User satisfaction scores

---

## **9. RISK ASSESSMENT & MITIGATION**

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|-----------|
| **EPSG Database Outdated** | Stale CRS recommendations | Medium | Regular pyproj updates, version pinning strategy |
| **Nominatim API Downtime** | Inability to resolve area names | Medium | Fallback to bounding box input, caching, monitoring |
| **LLM Hallucination** | Inaccurate geodetic advice | Medium | Constrained prompting, tool validation, testing |
| **API Rate Limits** | Service degradation | Low | Caching, request batching, quota management |
| **Coordinate Precision Loss** | Transformation errors | Low | Documentation of precision limits, validation |
| **Dependency Conflicts** | Installation/runtime issues | Low | Version pinning, virtual environments, CI testing |

---

## **10. ACCEPTANCE CRITERIA (MVP)**

**Minimum Viable Product Definition:**

The system is production-ready when:

1. **Core Functionality**
   - [ ] User can query CRS by area name in natural language
   - [ ] User can look up EPSG codes and get accurate metadata
   - [ ] User can transform coordinates between two CRS
   - [ ] Agent provides geodetic reference frame recommendations
   - [ ] 90%+ query success rate in manual testing

2. **Code Quality**
   - [ ] All tools have unit tests
   - [ ] >75% code coverage
   - [ ] No critical linting errors
   - [ ] Error handling for all failure modes

3. **Documentation**
   - [ ] README with setup instructions
   - [ ] Tool API documentation
   - [ ] Architecture documentation
   - [ ] Troubleshooting guide
   - [ ] Configuration guide

4. **User Experience**
   - [ ] Clear error messages for user errors
   - [ ] Reasonable response times (<5s)
   - [ ] Helpful context in agent responses
   - [ ] Support for multiple query formats

5. **Deployment**
   - [ ] Docker containerization support
   - [ ] Environment configuration system
   - [ ] Monitoring/logging capability
   - [ ] Deployment documentation

---

## **11. RESOURCE REQUIREMENTS**

### **Development Team**
- 1 Senior Python Developer (architect, lead)
- 1-2 Mid-level Python Developers (implementation)
- 1 QA Engineer (testing)
- 0.5 DevOps Engineer (CI/CD, deployment)
- 0.5 Technical Writer (documentation)

### **Infrastructure**
- Git repository (GitHub)
- CI/CD platform (GitHub Actions)
- Development VMs (as needed)
- Chat interface hosting (for MVP: Free tier sufficient)
- Monitoring tools (logging, error tracking)

### **Tools & Services**
- Google Cloud Platform (Gemini API)
- OpenStreetMap/Nominatim (free tier)
- Python dependencies (open source)
- GitHub (repository hosting)
- Development IDEs/editors

---

## **12. GLOSSARY OF GEODETIC TERMS**

| Term | Definition |
|------|-----------|
| **CRS** | Coordinate Reference System - framework for measuring/locating positions |
| **EPSG** | European Petroleum Survey Group - maintains geodetic registry |
| **Datum** | Reference surface from which coordinates are measured |
| **Projection** | Mathematical transformation from spherical to planar coordinates |
| **Reference Frame** | Fundamental geodetic system (e.g., WGS84, NAD83) |
| **AOI** | Area of Interest - geographic region of focus |
| **Transformation** | Converting coordinates from one CRS to another |
| **Ellipsoid** | Mathematical model of Earth's shape for a datum |
| **Zone** | Geographic subdivisions in certain projections (UTM zones) |
| **False Easting/Northing** | Offset values added to projected coordinates |

---

## **CONCLUSION**

The Geodetic AI-visor project aims to solve a real challenge in geospatial work: making expert-level geodetic knowledge accessible and actionable through conversational AI. The current implementation provides a solid foundation with core tools and agent infrastructure. The phased development plan ensures controlled growth from MVP to a sophisticated production system capable of supporting enterprise geospatial workflows.

**Next Immediate Action**: Begin Phase 2 implementation with enhanced error handling, expanded test suite, and improved documentation, targeting Q2 2026 completion.
