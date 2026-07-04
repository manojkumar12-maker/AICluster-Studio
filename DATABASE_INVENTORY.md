# AICluster Database Inventory

## Overview

**Engine**: SQLite via aiosqlite (async)
**ORM**: SQLAlchemy 2.0 Async with DeclarativeBase
**File location**: `backend/data/aicluster.db` (at runtime)
**Total tables**: 50+

---

## 1. Core Tables

### users
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | String (UUID) | PK | User identifier |
| username | String | UNIQUE, NOT NULL | Login username |
| hashed_password | String | NOT NULL | bcrypt hash |
| role | String | Default 'developer' | ADMIN, DEVELOPER, VIEWER |
| is_active | Boolean | Default true | Account active flag |
| created_at | DateTime | NOT NULL | Account creation timestamp |

**Relationships**: Referenced by `jobs.created_by`
**Indexes**: username (unique)
**Used by**: AuthService, auth API routes

---

### workers
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | String (UUID) | PK | Worker identifier |
| worker_name | String | UNIQUE, NOT NULL | Human-readable name |
| hostname | String | NOT NULL | Machine hostname |
| ip | String | NOT NULL | IP address |
| status | String | Default 'offline' | ONLINE, OFFLINE, BUSY, PAUSED, ERROR |
| cpu_percent | Float | Default 0 | CPU utilization |
| ram_percent | Float | Default 0 | RAM utilization |
| disk_percent | Float | Default 0 | Disk utilization |
| temperature | Float | Nullable | CPU temperature |
| network_speed | Float | Default 0 | Network throughput |
| current_job | String | Nullable | Currently assigned job ID |
| version | String | Default '1.0.0' | Worker software version |
| cpu_limit | Integer | Default 25 | CPU load limit % |
| ram_limit | Integer | Default 8 | RAM limit GB |
| priority | Integer | Default 0 | Worker selection priority |
| is_paused | Boolean | Default false | Paused by admin |
| last_seen | DateTime | NOT NULL | Last heartbeat timestamp |
| registered_at | DateTime | NOT NULL | First registration |

**Relationships**: `current_job` -> jobs.id (implicit FK)
**Used by**: WorkerManagerService, worker API routes, dashboard

---

### jobs
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | String (UUID) | PK | Job identifier |
| type | String | NOT NULL | Job type (echo, sleep, etc.) |
| status | String | NOT NULL | QUEUED, RUNNING, COMPLETED, FAILED, CANCELLED |
| assigned_worker | String | Nullable | Assigned worker ID |
| progress | Float | Default 0 | Progress 0-100 |
| payload | JSON | Default '{}' | Job input parameters |
| result | Text | Nullable | Job output |
| error | Text | Nullable | Error message on failure |
| logs | Text | Nullable | Execution logs |
| priority | Integer | Default 2 | 1=LOW, 2=MEDIUM, 3=HIGH, 4=CRITICAL |
| retry_count | Integer | Default 0 | Current retry attempt |
| max_retries | Integer | Default 3 | Maximum retries |
| created_at | DateTime | NOT NULL | Creation timestamp |
| started_at | DateTime | Nullable | Execution start |
| finished_at | DateTime | Nullable | Completion/failure |

**Indexes**: (priority, created_at)
**Relationships**: `assigned_worker` -> workers.id (implicit FK)
**Used by**: SchedulerService, job API routes

---

### system_logs
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | String (UUID) | PK | Log entry identifier |
| level | String | NOT NULL | INFO, WARNING, ERROR, DEBUG |
| message | Text | NOT NULL | Log message |
| source | String | NOT NULL | Component name |
| created_at | DateTime | NOT NULL | Timestamp |

**Indexes**: (level, created_at)
**Used by**: LogService, log API routes

---

## 2. Workflow Tables

### workflows
| Column | Description |
|--------|-------------|
| id, name, description, status | Workflow metadata |
| dag_data (JSON) | DAG structure |
| created_at, started_at, finished_at | Timeline |
| error | Failure details |

### workflow_tasks
| Column | Description |
|--------|-------------|
| id, workflow_id (FK) | Task identity |
| task_type, status | Type and state |
| assigned_worker | Worker assignment |
| input_data (JSON), output_data (JSON) | I/O payloads |
| cpu_required, ram_required, gpu_required | Resource requirements |
| priority, timeout_seconds | Execution params |
| progress, retry_count, max_retries | Progress tracking |
| created_at, started_at, finished_at | Timeline |

### task_dependencies
| Column | Description |
|--------|-------------|
| id, task_id (FK), depends_on_task_id (FK) | DAG edges |
| dependency_type | E.g. 'completion', 'success' |

### workflow_results
| Column | Description |
|--------|-------------|
| id, workflow_id (FK), status | Outcome |
| output_data (JSON), error | Result |
| started_at, finished_at | Timing |

### artifacts
| Column | Description |
|--------|-------------|
| id, workflow_id (FK), task_id (FK) | Ownership |
| name, type, path, size_bytes | File metadata |
| mime_type, checksum | Content info |
| metadata (JSON) | Arbitrary metadata |
| created_at | Timestamp |

### execution_metrics
| Column | Description |
|--------|-------------|
| id, workflow_id (FK), task_id (FK) | Ownership |
| cpu_usage, ram_usage, disk_usage | Resource consumption |
| execution_time_ms, tokens_used | Performance |
| timestamp | Collection time |

### cache
| Column | Description |
|--------|-------------|
| id, workflow_id (FK), task_id (FK) | Ownership |
| cache_key (unique), input_hash | Lookup |
| output_data (JSON), created_at | Cached result |
| ttl_seconds | Expiration |

### workflow_events
| Column | Description |
|--------|-------------|
| id, workflow_id (FK) | Ownership |
| event_type, data (JSON) | Event details |
| timestamp | When it happened |

### worker_capabilities
| Column | Description |
|--------|-------------|
| id, worker_id | Ownership |
| capability | Capability name |
| value | Capability value |
| updated_at | Last updated |

---

## 3. Repository Tables

### repositories
| Column | Description |
|--------|-------------|
| id, name, path, description | Repository identity |
| language, status | Language and scan state |
| file_count, total_size_bytes | Summary stats |
| last_scanned_at, created_at | Timelines |

### repository_files
| Column | Description |
|--------|-------------|
| id, repository_id (FK) | Ownership |
| path, filename, extension | File identity |
| language, size_bytes | File metadata |
| lines_of_code, complexity | Code metrics |
| last_modified, last_indexed | Timelines |
| checksum | File integrity |

### symbols
| Column | Description |
|--------|-------------|
| id, repository_id (FK), file_id (FK) | Location |
| name, symbol_type | Identity |
| signature, docstring | Details |
| line_start, line_end | Position |
| visibility, modifiers | Access control |

### symbol_imports
| Column | Description |
|--------|-------------|
| id, symbol_id (FK) | Owner |
| imported_name, source_module | Import details |
| import_type | Import kind |
| line_number | Location |

### symbol_references
| Column | Description |
|--------|-------------|
| id, symbol_id (FK), file_id (FK) | Reference location |
| line_number | Position |
| reference_type | Usage type |

### dependency_edges
| Column | Description |
|--------|-------------|
| id, repository_id (FK) | Repository |
| source_file_id (FK), target_file_id (FK) | Edge endpoints |
| dependency_type | Import, call, etc. |
| weight | Strength |

### code_metrics
| Column | Description |
|--------|-------------|
| id, repository_id (FK), file_id (FK) | Ownership |
| lines_of_code, comment_lines, blank_lines | Size metrics |
| cyclomatic_complexity, cognitive_complexity | Complexity |
| maintainability_index, cohesion | Quality metrics |
| coupling, instability, abstractness | Structural metrics |
| depth_of_inheritance, number_of_methods | OO metrics |
| duplicate_percentage, comment_ratio | Other |

### knowledge_nodes
| Column | Description |
|--------|-------------|
| id, repository_id (FK) | Repository |
| name, node_type | Identity and kind |
| content (JSON), embedding | Data |
| created_at, updated_at | Timelines |
| source_file_id, line_start, line_end | Location |

### knowledge_edges
| Column | Description |
|--------|-------------|
| id, source_node_id (FK), target_node_id (FK) | Edge |
| edge_type, weight | Relationship |
| metadata (JSON) | Extra info |
| created_at | Timestamp |

### repository_cache
| Column | Description |
|--------|-------------|
| id, repository_id (FK) | Ownership |
| cache_key, cache_value (JSON) | KV pair |
| expires_at, created_at | Expiration |

### repository_events
| Column | Description |
|--------|-------------|
| id, repository_id (FK) | Repository |
| event_type, data (JSON) | Event details |
| timestamp | When |

---

## 4. AI Tables

### ai_models
| Column | Description |
|--------|-------------|
| id, name, provider | Model identity |
| model_type | Chat, completion, embedding |
| context_window, max_tokens | Capacity |
| capabilities (JSON) | Feature flags |
| is_loaded, is_default | State |
| api_url, api_key (encrypted) | Connection |
| loaded_at, registered_at | Timelines |

### ai_sessions
| Column | Description |
|--------|-------------|
| id, title | Session identity |
| model_id (FK), provider | Model used |
| token_count, message_count | Usage stats |
| context_window, max_tokens | Limits |
| system_prompt | Session system prompt |
| expires_at, created_at, updated_at | Timelines |

### ai_messages
| Column | Description |
|--------|-------------|
| id, session_id (FK) | Ownership |
| role | system, user, assistant, tool |
| content (Text) | Message text |
| tokens, timestamp | Usage and time |
| tool_calls (JSON) | Tool invocations |

### prompt_templates
| Column | Description |
|--------|-------------|
| id, name | Template identity |
| template_text | Template content |
| variables (JSON) | Variable definitions |
| category, tags | Classification |
| created_at, updated_at | Timelines |

### tool_definitions
| Column | Description |
|--------|-------------|
| id, name, description | Tool identity |
| parameters (JSON) | JSON schema params |
| handler | Python handler path |
| is_enabled | Active flag |

### tool_calls
| Column | Description |
|--------|-------------|
| id, session_id (FK), message_id (FK) | Context |
| tool_name, input_data (JSON) | Invocation |
| output_data (JSON), error | Result |
| duration_ms, timestamp | Performance |

### ai_memory
| Column | Description |
|--------|-------------|
| id, session_id (FK) | Context |
| key, value | KV pair |
| type | Memory type |
| created_at, expires_at | Expiration |

### ai_provider_config
| Column | Description |
|--------|-------------|
| id, provider_name | Provider |
| config (JSON) | Configuration |
| is_active | Active flag |
| priority | Fallback order |

### runtime_metrics
| Column | Description |
|--------|-------------|
| id, session_id (FK), model_id (FK) | Context |
| tokens_in, tokens_out | Token counts |
| latency_ms, total_duration_ms | Timing |
| timestamp | Collection time |

---

## 5. Agent Tables

### agents
| Column | Description |
|--------|-------------|
| id, name, role | Identity and role |
| description, system_prompt | Configuration |
| capabilities (JSON), permissions (JSON) | Capabilities |
| model_id (FK), provider | LLM assignment |
| status | ONLINE, BUSY, PAUSED, DISABLED |
| max_concurrent_tasks | Limit |
| is_default, created_at | Metadata |

### agent_tasks
| Column | Description |
|--------|-------------|
| id, agent_id (FK) | Ownership |
| task_type, status | Type and state |
| input_data (JSON), output_data (JSON) | I/O |
| priority, assigned_by | Assignment |
| created_at, started_at, completed_at | Timeline |

### agent_messages
| Column | Description |
|--------|-------------|
| id, sender_id (FK), receiver_id (FK) | Communication |
| message_type, content (Text) | Message |
| parent_message_id | Threading |
| metadata (JSON), created_at | Extra info |

### agent_reviews
| Column | Description |
|--------|-------------|
| id, agent_id (FK), task_id (FK) | Context |
| reviewer_id (FK) | Reviewer |
| review_type, status | PASS, FAIL, NEEDS_WORK |
| comments (Text), score | Feedback |
| created_at, completed_at | Timeline |

### agent_merges
| Column | Description |
|--------|-------------|
| id, plan_id (FK) | Plan context |
| merge_type, status | Type and state |
| source_agent_id (FK), target_agent_id (FK) | Participants |
| input_data (JSON), output_data (JSON) | Merge content |
| conflicts (JSON) | Merge conflicts |
| created_at, completed_at | Timeline |

### agent_memory_store
| Column | Description |
|--------|-------------|
| id, agent_id (FK) | Context |
| key, value (JSON) | KV pair |
| type, scope | Classification |
| importance | Priority for retention |
| created_at, last_accessed_at, expires_at | Timelines |

### agent_metrics
| Column | Description |
|--------|-------------|
| id, agent_id (FK) | Context |
| metric_name, metric_value | Measurement |
| unit, tags (JSON) | Metadata |
| timestamp | Collection time |

---

## 6. Engineering Tables

### engineering_plans
| Column | Description |
|--------|-------------|
| id, title, description | Plan identity |
| goals (JSON), status | Objectives and state |
| risk_level, priority | Assessment |
| repository_id (FK) | Code context |
| created_at, updated_at, completed_at | Timeline |

### engineering_tasks
| Column | Description |
|--------|-------------|
| id, plan_id (FK) | Ownership |
| title, description | Task details |
| task_type | plan, implement, test, document |
| status | PENDING, IN_PROGRESS, COMPLETED, FAILED |
| agent_id (FK), priority | Assignment |
| input_data (JSON), output_data (JSON) | I/O |
| created_at, started_at, completed_at | Timeline |

### engineering_patches
| Column | Description |
|--------|-------------|
| id, plan_id (FK), task_id (FK) | Context |
| file_path, patch_content | Code changes |
| status, language | State and type |
| created_at, applied_at | Timeline |

### engineering_validations
| Column | Description |
|--------|-------------|
| id, plan_id (FK), task_id (FK) | Context |
| validation_type | syntax, lint, test, security |
| status | PASS, FAIL, WARNING |
| details (JSON), created_at | Results |

### engineering_repairs
| Column | Description |
|--------|-------------|
| id, plan_id (FK), task_id (FK) | Context |
| repair_type, status | Type and state |
| attempt_number, max_attempts | Retry tracking |
| input_data (JSON), output_data (JSON) | Repair content |
| created_at, completed_at | Timeline |

### engineering_quality
| Column | Description |
|--------|-------------|
| id, plan_id (FK) | Context |
| quality_dimension | code_quality, test_coverage, security |
| score, threshold | Evaluation |
| passed, details (JSON) | Result |
| checked_at | Timestamp |

### engineering_approvals
| Column | Description |
|--------|-------------|
| id, plan_id (FK) | Context |
| requested_by (FK), approved_by (FK) | Actors |
| status | PENDING, APPROVED, REJECTED |
| comments (Text), created_at | Metadata |

### engineering_metrics
| Column | Description |
|--------|-------------|
| id, plan_id (FK) | Context |
| total_tasks, completed_tasks, failed_tasks | Progress |
| total_duration_ms, avg_task_duration | Timing |
| repair_count, validation_pass_rate | Quality |
| created_at | Snapshot time |

### engineering_reports
| Column | Description |
|--------|-------------|
| id, plan_id (FK) | Context |
| report_type, content (JSON) | Report data |
| generated_at | Timestamp |

---

## 7. Studio Tables

### studio_workspaces
| Column | Description |
|--------|-------------|
| id, name, description | Workspace identity |
| root_path | File system root |
| owner_id (FK) -> users.id | Ownership |
| created_at, updated_at | Timeline |

### studio_projects
| Column | Description |
|--------|-------------|
| id, workspace_id (FK) | Parent workspace |
| name, description | Project identity |
| project_type, language | Classification |
| repository_id (FK) | Linked repo |
| created_at, updated_at | Timeline |

### studio_layouts
| Column | Description |
|--------|-------------|
| id, workspace_id (FK) | Context |
| name, layout_data (JSON) | Panel configuration |
| is_active, created_at, updated_at | State |

### studio_bookmarks
| Column | Description |
|--------|-------------|
| id, workspace_id (FK) | Context |
| name, target_type | File, symbol, line |
| target_data (JSON), created_at | Details |

### studio_preferences
| Column | Description |
|--------|-------------|
| id, workspace_id (FK) or user_id (FK) | Context |
| key, value (JSON) | Preference pair |
| scope | user, workspace |

### studio_history
| Column | Description |
|--------|-------------|
| id, workspace_id (FK) | Context |
| action, target_type | Action info |
| target_id, details (JSON) | Reference |
| timestamp | When it happened |

---

## 8. Audit Tables

### audit_logs
| Column | Description |
|--------|-------------|
| id, event_type, category, severity | Classification |
| message | Human-readable description |
| user_id, username | User context |
| worker_id, workflow_id, repository_id | Resource refs |
| plugin_id, agent_id, session_id | More refs |
| resource_type, resource_id, action | Target |
| status, duration_ms | Outcome |
| ip_address | Originating IP |
| extra (JSON), old_value, new_value | Change details |
| request_id, trace_id | Correlation |
| timestamp | When it happened |

### audit_settings
| Column | Description |
|--------|-------------|
| id, retention_days, max_log_entries | Retention |
| auto_purge, export_format | Automation |
| updated_at | Last update |

### audit_exports
| Column | Description |
|--------|-------------|
| id, format, status | Export job |
| filters (JSON), file_path | Content |
| created_at, completed_at | Timeline |
| row_count, file_size | Summary |

### audit_retention
| Column | Description |
|--------|-------------|
| id, purged_at, purged_before | Purge record |
| rows_purged, retention_days_at_purge | Stats |
| status | Outcome |
