# SARVANETRA — AUTONOMOUS AI VISION & ANALYTICS ENGINEERING MISSION

## Mission Type

Autonomous engineering, AI research, model evaluation, inference implementation, integration, benchmarking, testing and documentation mission.

## Precondition

This mission starts ONLY after the:

**SARVANETRA — MASTER AUTONOMOUS ENGINEERING & TENDER READINESS MISSION**

has been completed or has reached a stable enough state that the SARVANETRA core platform can be safely extended.

The Master Mission should have established:

* stable repository state
* functioning core VMS
* functional MediaMTX
* recording pipeline
* MinIO
* Kafka
* PostgreSQL
* FastAPI
* authentication/RBAC
* edge NVR foundation
* automated tests
* stabilized Kong/edge paths
* documented architecture
* tender implementation baseline

Do not assume the previous mission succeeded merely because it produced a report.

Verify the actual repository and runtime.

---

# 1. MISSION OBJECTIVE

Transform SARVANETRA from a primarily VMS/data/event platform into a:

# MODULAR OPEN-SOURCE AI SURVEILLANCE PLATFORM

capable of integrating AI perception and analytics for the requirements identified in:

* `TENDER_COMPARISON.md`
* `TENDER_READINESS.md`
* `TENDER_REQUIREMENTS.md`
* `TENDER_ROADMAP.md`

The target architecture is:

```text
CAMERA
   │
   ▼
MediaMTX
   │
   ├──────────────────────► RECORDING
   │                           │
   │                           ▼
   │                         MinIO
   │
   ▼
AI INFERENCE LAYER
   │
   ├── Object Detection
   ├── Tracking
   ├── ANPR
   ├── Vehicle Classification
   ├── Pose / Fall
   ├── Line Crossing
   ├── Loitering
   ├── Abandoned Object
   ├── People Counting
   ├── Queue Analytics
   ├── Crowd Density
   ├── Face Search
   └── Other Analytics
   │
   ▼
EVENT NORMALIZATION
   │
   ▼
KAFKA
   │
   ├── PostgreSQL
   ├── Alert Engine
   ├── Watchlist
   ├── Parking
   ├── Incident Management
   ├── ICCC / GIS
   └── Evidence
```

The AI layer must remain **replaceable**.

The SARVANETRA core must not depend on a particular AI vendor, model family or inference framework.

---

# 2. NON-NEGOTIABLE OPEN-SOURCE POLICY

## VERY IMPORTANT

This project has:

**NO COMMERCIAL AI OR MODEL LICENSES AVAILABLE.**

Therefore the development and production candidate stack must be based on:

```text
Open-source software
+
appropriately licensed model weights
+
open/usable inference runtime
```

Do not assume "open source" automatically means commercial use is permitted.

For EVERY AI dependency, independently verify:

1. source-code license
2. model license
3. pretrained-weight license
4. commercial-use rights
5. redistribution rights
6. modification rights
7. attribution requirements
8. restrictions on derivative works
9. restrictions on model redistribution
10. relevant training-data/model terms where available

### Classification

Every evaluated model must be classified as:

```text
PRODUCTION-CANDIDATE
PROTOTYPE-ONLY
LICENSE-UNCERTAIN
REJECTED
```

Do not place an uncertain or non-commercial-only model into the production candidate stack.

Do not purchase or assume a commercial license.

Do not silently substitute a proprietary cloud API.

Do not use an enterprise-only dependency.

---

# 3. MODEL LICENSE AUDIT

Create:

```text
docs/AI_MODEL_LICENSE_MATRIX.md
```

For every evaluated model/framework, record:

```text
Capability
Model
Repository
Version / Commit
Code License
Weight License
Commercial Use
Redistribution
Modification
Model Distribution
Runtime
GPU Requirements
CPU Support
Status
Reason
```

The audit must distinguish:

```text
framework license
≠
model license
≠
pretrained weight license
```

If a model repository is permissively licensed but its pretrained weights are restricted:

mark the model accordingly.

Do not package it.

---

# 4. INITIAL REPOSITORY / PLATFORM GATE

Before beginning AI implementation:

1. Read:

   * `PROJECT_STATE.md`
   * `PROJECT_ROADMAP.md`
   * `TENDER_COMPARISON.md`
   * `TENDER_READINESS.md`
   * `TENDER_REQUIREMENTS.md`
   * `TENDER_ROADMAP.md`
2. Read the previous Master Mission final report.
3. Inspect Git status.
4. Inspect current branch and commit.
5. Confirm the previous mission's important changes.
6. Run the existing tests.
7. Run core service health checks.
8. Verify Docker Compose state.

If critical SARVANETRA functionality is broken:

fix it first.

The AI layer must never be used to hide a broken VMS core.

---

# 5. AI ARCHITECTURE PRINCIPLE

SARVANETRA is:

```text
VMS
+
DATA
+
EVENT BUS
+
ACCESS CONTROL
+
WORKFLOW
+
COMMAND CENTRE
+
EVIDENCE
```

The AI system is:

```text
PERCEPTION
+
INFERENCE
+
TRACKING
+
ANALYTICS
```

Do NOT make FastAPI directly perform long-running inference.

Use dedicated workers/services.

Do NOT make AI responsible for video recording.

Do NOT make recording depend on AI availability.

If AI crashes:

```text
Camera remains available
Recording continues
Playback continues
Core API continues
```

AI should recover independently.

---

# 6. PARALLEL AGENT ORGANIZATION

Use parallel agents/subagents aggressively.

Recommended structure:

```text
                         AI LEAD
                            │
       ┌────────────────────┼─────────────────────┐
       │                    │                     │
 Model Research       Platform Integration    QA/Validation
       │                    │                     │
 ┌─────┼─────┐        ┌─────┼─────┐          ┌────┼────┐
 │     │     │        │     │     │          │    │    │
ANPR  CV   Crowd     Kafka Backend Frontend  Load Chaos Security
 │     │     │
Face Tracking Forecast
```

Suggested specialist agents:

* AI Architecture Agent
* Model Research Agent
* Model Licensing Agent
* Frigate Evaluation Agent
* Object Detection Agent
* Tracking Agent
* ANPR Agent
* Vehicle Analytics Agent
* Pose/Fall Agent
* Crowd Analytics Agent
* Forecasting Agent
* Face/Embedding Agent
* GPU/Runtime Agent
* Kafka Integration Agent
* Backend Integration Agent
* Frontend Integration Agent
* Security/Privacy Agent
* QA Agent
* Performance Agent

Use isolated branches/worktrees when multiple agents modify source code.

Do not allow multiple agents to edit the same core files simultaneously without coordination.

---

# 7. HARDWARE DISCOVERY

Inspect the actual development environment.

Determine:

```text
CPU
CPU cores
RAM
disk
GPU
GPU model
VRAM
NVIDIA driver
CUDA
cuDNN
TensorRT
Docker GPU support
OpenCL/Vulkan if relevant
```

Run actual commands.

Do not assume a GPU exists.

Create:

```text
docs/AI_HARDWARE_CAPABILITY.md
```

Provide profiles:

```text
CPU-only development
GPU development
Edge inference
Central GPU server
```

Identify realistic constraints.

---

# 8. FRIGATE EVALUATION

Evaluate **Frigate** as a candidate general-purpose AI perception component.

Do NOT replace MediaMTX with Frigate.

The experiment should test:

```text
Camera
 ↓
MediaMTX
 ├── recording → MinIO
 │
 └── detection stream → Frigate
                        ↓
                   AI Detection
                        ↓
                     Events
                        ↓
                     MQTT
                        ↓
                 AI Event Adapter
                        ↓
                      Kafka
                        ↓
                  SARVANETRA
```

Evaluate whether Frigate can provide useful primitives for:

* object detection
* camera zones
* tracking
* motion-assisted detection
* event generation
* hardware acceleration
* RTSP processing

Determine where Frigate is useful and where it is insufficient.

Do not force Frigate into the architecture if the experiment demonstrates that a dedicated inference runtime is better.

Create:

```text
docs/FRIGATE_EVALUATION.md
```

Include:

```text
Strengths
Weaknesses
License
Detector compatibility
Runtime compatibility
Kafka integration approach
MQTT integration approach
GPU usage
CPU usage
Latency
Scaling
Suitability
Decision
```

The decision must be evidence-based.

---

# 9. AI MODEL RESEARCH

Evaluate open-source candidates across the following capability groups:

```text
Object Detection
Tracking
ANPR / OCR
Vehicle Classification
Vehicle Attributes
Pose Estimation
Fall Detection
People Counting
Queue Analytics
Crowd Density
Face Detection
Face Embedding
ReID
Action Recognition
Forecasting
```

Do not choose models purely because they are popular.

Evaluate:

```text
license
weights
accuracy
latency
memory
GPU compatibility
CPU fallback
deployment complexity
community maturity
maintenance
Indian CCTV suitability
camera resolution
night performance
crowded-scene performance
```

---

# 10. MODEL EVALUATION RULE

For each candidate model:

1. Obtain the source.
2. Verify its license.
3. Obtain the model only if permitted.
4. Record checksum/version.
5. Install its runtime.
6. Run inference.
7. Benchmark it.
8. Compare alternatives.
9. Decide whether it is:

   * production candidate
   * prototype
   * rejected

Do not install 50 large models indiscriminately.

Choose a small number of serious candidates per capability.

---

# 11. GENERAL OBJECT DETECTION

Build a reusable object detector service.

Required base classes should include:

```text
person
bicycle
motorcycle
car
bus
truck
```

Allow extensibility.

Output standardized events:

```json
{
  "event_id": "...",
  "event_type": "person.detected",
  "event_version": "1.0",
  "timestamp": "...",
  "camera_id": "...",
  "site_id": "...",
  "model_name": "...",
  "model_version": "...",
  "class": "person",
  "confidence": 0.94,
  "bbox": [x1, y1, x2, y2],
  "source": "ai-worker"
}
```

---

# 12. TRACKING

Build a generic tracking layer.

Support:

* track ID
* object class
* bounding box
* timestamp
* trajectory
* velocity estimate where reasonable
* dwell time

The tracker must be replaceable.

Use it as the primitive for:

```text
loitering
line crossing
people counting
queue analytics
vehicle tracking
behavior analytics
```

Do not duplicate tracking code inside each analytics module.

---

# 13. INTRUSION DETECTION

Implement configurable ROI-based intrusion.

Pipeline:

```text
Object Detection
→ Object class
→ ROI
→ Entry
→ Rule
→ Event
```

Support:

* polygon zones
* object class filters
* direction
* confidence threshold
* cooldown

Produce:

```text
intrusion.detected
```

---

# 14. LINE CROSSING

Implement virtual tripwire analytics.

Support:

```text
A → B
B → A
both directions
```

For:

* persons
* vehicles

Produce:

```text
line_crossing.detected
```

Use track trajectories rather than frame-by-frame object counting.

---

# 15. LOITERING

Implement:

```text
track
→ ROI
→ dwell timer
→ threshold
→ loitering event
```

Parameters:

```text
ROI
minimum dwell time
object type
minimum confidence
cooldown
```

Do not train a separate neural model if detector + tracker + rule engine is sufficient.

---

# 16. ABANDONED OBJECT

Implement an architecture for:

```text
object
→ stationary state
→ person/object association
→ owner leaves
→ dwell threshold
→ abandoned_object
```

Use configurable thresholds.

Suppress obvious temporary false positives.

---

# 17. FALL DETECTION

Evaluate pose-based approaches.

Pipeline:

```text
Person Detection
→ Pose
→ Temporal Sequence
→ Body Orientation
→ Rule/Classifier
→ Fall Event
```

Do not trigger a fall alert from a single frame.

Test:

* standing
* sitting
* bending
* lying
* falling
* partial occlusion

Measure false positives where possible.

---

# 18. ABNORMAL / SUSPICIOUS BEHAVIOR

Do NOT equate:

```text
person detected
```

with:

```text
suspicious behavior
```

Evaluate approaches based on:

* trajectories
* dwell time
* unusual movement
* temporal patterns
* pose/action sequences

Initially implement a modular framework that can support:

```text
rule-based anomaly
+
future ML model
```

Explicitly label prototype behavior as prototype.

---

# 19. VEHICLE CLASSIFICATION

Support:

```text
car
bus
truck
LMV
HMV
motorcycle
scooter
2-wheeler
3-wheeler
```

Separate:

```text
object detection
vehicle classification
vehicle attributes
```

Do not embed business classifications directly into model code.

Use configurable mappings.

---

# 20. VEHICLE ATTRIBUTES

Build an interface for:

```text
color
make
model
body type
```

Do not claim accurate make/model recognition until it is benchmarked.

Store:

```text
attribute
confidence
model
version
```

---

# 21. HELMET / TRIPLE-RIDING

Create a modular analytics pipeline:

```text
Motorcycle
→ Rider Detection
→ Person Count
→ Helmet Detection
→ Rule Engine
→ Violation
```

Support:

```text
helmet missing
triple riding
```

Do not assume the inference result is legally sufficient evidence.

Record confidence and evidence.

---

# 22. ANPR ARCHITECTURE

Build ANPR as a dedicated pipeline:

```text
RTSP
 ↓
Vehicle Detection
 ↓
Plate Detection
 ↓
Plate Crop
 ↓
OCR
 ↓
Character Normalization
 ↓
Confidence
 ↓
ANPR Transaction
 ↓
Kafka
```

Separate:

```text
plate detector
OCR
plate normalization
transaction storage
watchlist matching
```

Do not couple ANPR to FastAPI.

---

# 23. ANPR DATA CONTRACT

Create:

```text
vehicle.anpr.detected
```

with an extensible schema containing:

```text
event_id
timestamp
camera_id
site_id
plate
confidence
vehicle_type
vehicle_color
vehicle_make
vehicle_model
snapshot_key
video_reference
source
model_name
model_version
```

Fields may be optional when the relevant model is unavailable.

---

# 24. ANPR DATABASE

Ensure SARVANETRA has:

```text
anpr_transaction
vehicle_watchlist
```

or the equivalent structures from the previous mission.

Support:

* search
* filter
* date range
* camera
* site
* vehicle type
* confidence
* watchlist status

---

# 25. ANPR NORMALIZATION

Normalize Indian plate OCR variations.

Handle:

* spaces
* punctuation
* case
* common OCR substitutions
* malformed strings

Do not corrupt original evidence.

Store:

```text
original OCR result
normalized value
correction history
```

---

# 26. FUZZY PLATE SEARCH

Use PostgreSQL search functionality such as `pg_trgm` where appropriate.

Test:

```text
exact
1-character difference
2-character difference
common OCR substitutions
case differences
spacing differences
large datasets
```

Benchmark queries.

---

# 27. WATCHLIST PIPELINE

Implement:

```text
ANPR event
→ Kafka
→ watchlist matcher
→ match
→ alert
→ audit
→ evidence
```

Support:

```text
Wanted
Stolen
Suspicious
Whitelist
Blacklist
Custom
```

Implement duplicate suppression.

Do not claim a measured alert latency until tested.

---

# 28. TENDER A ANPR REQUIREMENTS

Explicitly evaluate support for:

* high-speed recognition
* day/night
* rain
* fog
* dust
* glare
* accuracy benchmarks
* local edge inference

Treat external certification separately.

Do not claim that an open-source model alone satisfies:

```text
230 km/h requirement
ARAI certification
formal accuracy certification
```

Create:

```text
docs/ANPR_TENDER_A_VALIDATION.md
```

with:

```text
software capability
test evidence
hardware dependency
certification dependency
remaining gap
```

---

# 29. PEOPLE COUNTING

Build:

```text
person detection
→ tracking
→ tripwire
→ directional count
```

Support:

```text
entry
exit
bidirectional
hourly
daily
site aggregation
```

Publish:

```text
person.counted
```

---

# 30. QUEUE ANALYTICS

Build a modular queue pipeline:

```text
person detection
→ tracking
→ queue ROI
→ spatial clustering
→ queue size
→ wait-time estimate
```

Support configurable queue zones.

Do not fabricate wait-time accuracy.

---

# 31. CROWD DENSITY

Evaluate specialized density estimation models.

Candidate approaches may include density-map architectures identified in the tender analysis.

Measure:

```text
density estimation
GPU memory
latency
FPS
scaling
crowded-scene behavior
```

Produce:

```text
crowd.density.updated
```

with:

```text
camera
zone
persons_per_square_meter
density map reference
timestamp
model
confidence/quality information
```

---

# 32. CROWD HEATMAP

Implement frontend support for:

```text
trajectory coordinates
density coordinates
camera coordinates
GIS coordinates
```

Display:

```text
current density
historical heatmap
zone risk
movement
```

Do not mix camera-local pixel coordinates with GIS coordinates without a calibrated transformation.

---

# 33. CONGESTION RULE ENGINE

Implement:

```text
density
+
zone threshold
+
time threshold
=
congestion alert
```

Make thresholds configurable.

Separate:

```text
measurement
```

from:

```text
policy decision
```

---

# 34. PREDICTIVE ANALYTICS

Create a separate forecasting service.

Use historical:

```text
people count
vehicle count
parking occupancy
queue length
crowd density
```

Evaluate:

```text
baseline statistical model
ARIMA / similar
Prophet / similar
LSTM / equivalent
```

Only use complex models if they outperform sensible baselines.

Measure actual forecasting error.

Produce:

```text
predicted crowd
predicted queue
predicted occupancy
risk indicator
forecast horizon
uncertainty
```

Never represent predictions as observed facts.

---

# 35. FACE / MISSING PERSON

Design a separate biometric module:

```text
Face Detection
→ Alignment
→ Embedding
→ Vector Search
→ Similarity
→ Candidate
→ Evidence
```

Support:

* gallery
* enrollment
* search
* camera
* timestamp
* last-seen timeline

IMPORTANT:

Do not integrate any pretrained face model unless its model-weight terms are suitable for the intended use.

A permissively licensed code repository does not automatically make its pretrained weights suitable.

Maintain the license record.

---

# 36. RE-ID / MULTI-CAMERA TRACKING

Create a generic ReID interface.

Conceptual flow:

```text
Camera A
→ track
→ embedding
        ↓
   correlation
        ↓
Camera B
→ candidate track
```

Do not claim identity certainty.

Expose:

```text
candidate similarity
confidence
source cameras
timestamps
```

Only selected, properly licensed models may be production candidates.

---

# 37. JOURNEY INTELLIGENCE

Build a correlation layer capable of linking:

```text
ANPR
parking
people counting
queue
gate events
camera events
```

into:

```text
visitor/vehicle journey timeline
```

Do not require a single AI model for this.

This is primarily an event-correlation problem.

---

# 38. DRONE AI

Do not build a separate drone computer-vision architecture.

Reuse:

```text
MediaMTX RTMP
+
AI inference
+
Kafka events
+
GIS
```

A drone should behave as another video/event source.

Keep future telemetry integration independent through a MAVLink/event adapter.

---

# 39. AI EVENT CONTRACT VERSIONING

Create versioned schemas.

Topics should include, where relevant:

```text
vehicle.anpr.detected
vehicle.classified
vehicle.attribute.detected
person.detected
person.tracked
person.counted
intrusion.detected
line_crossing.detected
loitering.detected
abandoned_object.detected
fall.detected
behavior.anomaly.detected
crowd.density.updated
queue.updated
face.match.detected
```

Every event should support:

```text
event_id
event_type
event_version
timestamp
camera_id
site_id
model_name
model_version
confidence
source
evidence references
payload
```

Consumers must be designed for idempotency.

---

# 40. AI EVENT GATEWAY

Build a clean adapter between AI engines and Kafka.

Conceptually:

```text
Frigate
      \
ANPR ----\
Crowd ----> AI Event Gateway → Kafka
Face ----/
Custom ---/
```

The core platform should not need to know which engine generated the event.

---

# 41. MQTT → KAFKA ADAPTER

If Frigate is selected for some capabilities:

implement a small adapter:

```text
Frigate MQTT
→ schema normalization
→ Kafka
```

Do not expose MQTT as the public application integration contract.

Kafka remains the central event bus.

---

# 42. AI INFERENCE RUNTIME

Evaluate:

```text
ONNX Runtime
PyTorch
TensorRT
OpenCV
FFmpeg
```

where appropriate.

Use open-source runtimes.

Do not force one runtime for every model.

Create an abstraction such as:

```text
InferenceEngine
ModelRunner
Detector
Tracker
OCR
Embedder
ForecastModel
```

---

# 43. MODEL REGISTRY

Implement a simple registry/configuration.

Example:

```yaml
name: object-detector
version: 1.0
task: detection
runtime: ...
artifact: ...
checksum: ...
license: ...
input_size: ...
classes: ...
threshold: ...
device: gpu
enabled: true
```

Do not hard-code model filenames throughout the repository.

---

# 44. CAMERA ANALYTICS CONFIGURATION

Allow camera-specific configuration without rebuilding containers.

Example:

```yaml
camera_id: CAM001

analytics:
  object_detection: true
  tracking: true
  anpr: true
  intrusion: true
  line_crossing: true
  loitering: true
  helmet: false

regions:
  intrusion:
    - ...
  line_crossing:
    - ...
```

Support runtime configuration where practical.

---

# 45. FRAME PROCESSING ARCHITECTURE

Implement resource controls.

Support:

```text
frame sampling
batching
frame skipping
queue limits
backpressure
worker concurrency
```

Avoid:

```text
unbounded queues
unbounded memory
one model process per camera
```

Track dropped frames.

---

# 46. AI FAILURE ISOLATION

Test:

```text
AI worker crashes
GPU unavailable
model missing
model corrupt
Kafka down
RTSP down
MediaMTX down
worker OOM
inference queue overloaded
```

Verify:

```text
recording continues
VMS continues
camera management continues
AI resumes when available
```

---

# 47. GPU BENCHMARKING

Where GPU is available, benchmark:

```text
GPU utilization
VRAM
decoder utilization
inference latency
FPS
streams
batch size
```

Test multiple concurrency levels.

Do not claim:

```text
100 cameras/GPU
500 cameras/GPU
```

unless actual measurements support it.

---

# 48. CPU FALLBACK

Where practical provide a CPU-only path for:

* development
* unit tests
* synthetic event testing
* environments without GPU

Clearly distinguish CPU proof-of-concept from production inference capacity.

---

# 49. SCALE TESTING

Where practical simulate:

```text
10 cameras
25 cameras
50 cameras
100 cameras
```

Measure:

```text
events/sec
latency
CPU
RAM
GPU
VRAM
dropped frames
Kafka lag
```

Create:

```text
docs/AI_SCALE_TEST_REPORT.md
```

---

# 50. AI TEST DATASET STRUCTURE

Create a reusable dataset/evaluation structure.

Suggested categories:

```text
anpr/
    day/
    night/
    rain/
    glare/
    blur/
    occlusion/

people/
    normal/
    crowded/
    queue/

vehicles/
    car/
    bike/
    bus/
    truck/

behavior/
    intrusion/
    loitering/
    abandoned/
    fall/
```

Do not fabricate annotated datasets.

Clearly distinguish:

```text
real dataset
public dataset
synthetic dataset
unlabeled test footage
```

---

# 51. ANPR TEST DATA

For ANPR, test:

```text
Indian plates
different fonts/layouts
day
night
headlights
blur
occlusion
angled views
low resolution
dirty plates
partial plates
rain
fog
fast motion
```

Measure actual results.

Do not label a development result as tender compliance.

---

# 52. AI DEMONSTRATION VIDEOS

Create an AI demo pipeline capable of:

```text
image → inference
video → inference
RTSP → inference
```

Produce:

```text
annotated video
event JSON
latency report
FPS report
```

This will be used later for tender demonstrations.

---

# 53. AI DASHBOARD

Add an AI operations interface.

Display:

```text
AI worker health
model
version
camera count
FPS
latency
GPU utilization
VRAM
events/sec
errors
dropped frames
```

Allow authorized users to configure:

* analytics enabled
* confidence
* ROI
* threshold
* cooldown

Do not expose infrastructure controls to ordinary users.

---

# 54. AI EVENT VISUALIZATION

Integrate AI events into ICCC.

Support:

```text
intrusion
loitering
fall
ANPR
watchlist
crowd alert
queue alert
```

Display:

* timestamp
* camera
* site
* event
* confidence
* evidence

---

# 55. AI EVIDENCE

AI events must link to:

```text
snapshot
video
timestamp
camera
event
model
confidence
```

Do not duplicate large video files when a reference to existing MinIO objects is sufficient.

---

# 56. PRIVACY ARCHITECTURE

Identify AI-generated sensitive information:

```text
license plates
faces
face embeddings
person trajectories
vehicle images
```

Implement or design:

```text
access control
retention
deletion
audit
redaction
evidence handling
```

Do not expose biometric embeddings to normal users.

Do not put sensitive raw data in logs.

Create:

```text
docs/AI_PRIVACY_ARCHITECTURE.md
```

---

# 57. AI SECURITY

Audit:

* model artifacts
* internal AI APIs
* Kafka topics
* MQTT
* inference containers
* service credentials
* evidence access
* model loading

Do not allow arbitrary model upload or arbitrary executable inference code through the user-facing application.

---

# 58. SUPPLY-CHAIN SECURITY

Record:

```text
source repository
commit/version
container image
base image
Python/package versions
model checksum
```

Generate or document an SBOM where practical.

Avoid unpinned critical dependencies.

---

# 59. AI OBSERVABILITY

Expose metrics for:

```text
worker health
model health
FPS
latency
queue depth
events/sec
errors
dropped frames
GPU memory
GPU utilization
model version
```

The operator must be able to answer:

```text
Is AI alive?
Which model is running?
How many cameras are being processed?
Is AI falling behind?
Are frames being dropped?
Are events reaching Kafka?
```

---

# 60. AI → KAFKA → SARVANETRA END-TO-END

At minimum establish complete demonstrable paths for:

## Path 1

```text
video
→ detector
→ tracker
→ line crossing
→ Kafka
→ FastAPI
→ PostgreSQL
→ ICCC
```

## Path 2

```text
video
→ vehicle
→ plate
→ OCR
→ ANPR
→ Kafka
→ watchlist
→ alert
→ evidence
```

## Path 3

```text
video
→ person detection
→ counting
→ Kafka
→ occupancy
→ dashboard
```

## Path 4

```text
video
→ crowd model
→ density
→ Kafka
→ risk rule
→ alert
→ ICCC
```

---

# 61. AI SIMULATOR

Build an AI event simulator.

Support:

```text
person
vehicle
plate
intrusion
loitering
fall
crowd
queue
face match
```

It must use the same event contracts as real inference workers.

This provides:

* backend testing
* frontend testing
* Kafka testing
* demonstration
* load testing

without requiring physical cameras.

---

# 62. AI CHAOS TESTING

Simulate:

```text
AI worker failure
model failure
GPU failure
Kafka outage
camera outage
RTSP reconnect
high event load
slow inference
memory pressure
invalid frame
model artifact missing
```

Document:

```text
expected behavior
actual behavior
recovery behavior
```

Create:

```text
docs/AI_CHAOS_TEST_REPORT.md
```

---

# 63. AI MODEL COMPARISON

For each major capability, create a comparison.

Example:

```text
Capability: Object Detection

Candidate A
Candidate B
Candidate C

Metrics:
License
Weights
Accuracy
FPS
Latency
VRAM
CPU
Deployment complexity
Commercial suitability
Indian CCTV suitability
```

Do this for:

* object detection
* OCR/ANPR
* tracking
* pose
* crowd
* face/embedding
* forecasting

---

# 64. OPEN-SOURCE PRODUCTION STACK

At the end of evaluation, establish:

```text
Production Candidate
```

for each capability.

Do not force a single model family across all tasks.

The final architecture may legitimately use:

```text
Detector A
+
OCR B
+
Tracker C
+
Crowd Model D
+
Forecast Model E
```

provided the licensing and deployment requirements are satisfied.

---

# 65. NO COMMERCIAL DEPENDENCY FALLBACK

For every capability that cannot currently be satisfied with an appropriately licensed open-source model:

do NOT silently substitute a proprietary model.

Instead build:

```text
Adapter Interface
+
Synthetic Test Implementation
+
Documentation
```

and mark:

```text
EXTERNAL / FUTURE MODEL DEPENDENCY
```

This is preferable to creating a legally unusable implementation.

---

# 66. TENDER A AI TRACEABILITY

Create:

```text
docs/AI_TENDER_A_TRACEABILITY.md
```

Map:

```text
T1-ANPR-001
T1-ANPR-002
T1-ANPR-003
T1-ANPR-007
T1-ANPR-008
T1-ANPR-009
T1-ANPR-010
T1-ANPR-011
...
```

to:

```text
AI component
model
event
backend
frontend
test
evidence
license
external dependency
status
```

Explicitly distinguish certification requirements.

---

# 67. TENDER B AI TRACEABILITY

Create:

```text
docs/AI_TENDER_B_TRACEABILITY.md
```

Map AI requirements including:

```text
intrusion
line crossing
loitering
abandoned object
fall
abnormal behavior
object classification
ReID
people counting
queue analytics
crowd density
predictive analytics
ANPR
face search
```

to:

```text
model
runtime
event
Kafka topic
backend
UI
test
status
```

The tender requirements explicitly identify these areas as AI/ML or analytics requirements.

---

# 68. CERTIFICATION DISTINCTION

Never claim:

```text
AI model works
=
tender compliance
```

Maintain separate statuses:

```text
software implemented
prototype demonstrated
benchmark measured
field validated
OEM certified
external certification required
```

In particular, do not claim:

* ARAI certification
* certified ANPR speed performance
* certified accuracy
* formal security certification

without the relevant evidence.

---

# 69. PRODUCTION VS PROTOTYPE

Every AI component must explicitly carry one of:

```text
PRODUCTION-CANDIDATE
WORKING PROTOTYPE
SIMULATION
INTEGRATION READY
EXTERNAL DEPENDENCY
NOT IMPLEMENTED
```

Never hide prototype code behind a production-ready label.

---

# 70. MODEL VERSIONING

Record:

```text
model_name
model_version
artifact_checksum
runtime_version
configuration_version
```

Every AI-generated event should be attributable to the model version that produced it.

---

# 71. REPRODUCIBILITY

A second developer must be able to reproduce:

```text
environment
model installation
inference
benchmark
event generation
```

from documentation.

Create:

```text
docs/AI_SETUP.md
docs/AI_DEVELOPMENT.md
docs/AI_BENCHMARKING.md
docs/AI_DEMO_RUNBOOK.md
```

---

# 72. AI CONTAINERIZATION

Create clean container boundaries.

Potential structure:

```text
ai-platform/
    common/
    schemas/
    event-gateway/
    detectors/
    trackers/
    anpr/
    crowd/
    face/
    forecasting/
    simulators/
```

Adapt this structure to the existing repository architecture instead of blindly imposing it.

Each service must have:

* healthcheck
* logging
* resource limits where appropriate
* environment configuration
* clean shutdown
* failure handling

---

# 73. AI DEPLOYMENT PROFILES

Provide:

```text
AI_DEV_CPU
AI_DEV_GPU
AI_EDGE
AI_CENTRAL_GPU
```

Each profile should specify:

```text
models
runtime
device
resource limits
camera count
sampling
concurrency
```

---

# 74. EDGE AI DESIGN

The edge architecture should support:

```text
Camera
 ↓
Edge MediaMTX
 ↓
Edge AI
 ↓
Local event queue
 ↓
SQLite
 ↓
Hub synchronization
```

Use edge AI especially where network resilience is important.

ANPR should have an architecture capable of operating locally during network interruption, consistent with the Tender A requirement for local LPU processing.

---

# 75. CENTRAL AI DESIGN

Central processing should support:

```text
Hub MediaMTX
 ↓
AI Worker Pool
 ↓
Kafka
```

Use this for workloads suitable for centralized GPU infrastructure.

---

# 76. AI RESOURCE GOVERNANCE

Prevent AI from overwhelming SARVANETRA.

Implement or document:

* max streams per worker
* max queue depth
* frame sampling
* memory limits
* GPU limits
* retry limits
* backoff
* event rate controls

The VMS must remain operational if AI capacity is exceeded.

---

# 77. AI BENCHMARK REPORT

Create:

```text
docs/AI_MODEL_BENCHMARK.md
```

For every candidate record:

```text
Task
Model
Version
License
Hardware
Input
Resolution
FPS
Latency
VRAM
CPU
Accuracy metric
Dataset
Limitations
Decision
```

---

# 78. AI ARCHITECTURE DECISION

After experimentation, create:

```text
docs/AI_ARCHITECTURE_DECISION.md
```

Document:

```text
What we selected
What we rejected
Why
License reasoning
Performance reasoning
Hardware reasoning
Architecture reasoning
Migration path
Fallback
```

Do not select models based only on popularity.

---

# 79. PRINCIPAL AI ARCHITECT REVIEW

After implementation, spawn a fresh AI architect agent that did NOT design the original implementation.

Ask it to challenge:

```text
model selection
licenses
architecture
GPU use
Kafka
events
security
privacy
scalability
failure isolation
tender traceability
```

Create:

```text
docs/AI_PRINCIPAL_ARCHITECT_REVIEW.md
```

---

# 80. FINAL ADVERSARIAL PASS

Run a second independent pass.

Ask fresh agents:

> Assume the first team made serious mistakes. Find everything they missed.

Audit:

* licensing
* model choices
* false positives
* false negatives
* performance
* data integrity
* event duplication
* privacy
* security
* deployment
* edge failure
* Kafka failure
* model failure
* tender traceability

Fix genuine high-value issues.

---

# 81. FINAL DEMONSTRATION

Create an end-to-end synthetic demonstration:

```text
CAMERA
 ↓
MediaMTX
 ↓
AI DETECTION
 ↓
TRACKING
 ↓
LINE CROSSING
 ↓
PEOPLE COUNT
 ↓
ANPR
 ↓
WATCHLIST
 ↓
ALERT
 ↓
KAFKA
 ↓
POSTGRESQL
 ↓
ICCC
 ↓
EVIDENCE
```

Then:

```text
CROWD VIDEO
 ↓
DENSITY MODEL
 ↓
DENSITY EVENT
 ↓
CONGESTION RULE
 ↓
ALERT
 ↓
ICCC HEATMAP
```

And where a properly licensed/approved biometric model is available:

```text
FACE
 ↓
EMBEDDING
 ↓
VECTOR SEARCH
 ↓
CANDIDATE MATCH
 ↓
LAST-SEEN TIMELINE
 ↓
AUDIT
```

Use simulated data where physical cameras/models are unavailable.

Clearly label simulation.

---

# 82. TENDER DEMO MODE

Create a reproducible demonstration environment.

A fresh developer should be able to:

```text
clone
configure
start
generate synthetic video/events
open dashboard
demonstrate AI
```

without modifying application code.

Create:

```text
docs/AI_DEMO_RUNBOOK.md
```

---

# 83. TEST SUITE

Add automated tests for:

## AI event schemas

* validation
* versioning
* malformed event

## Detection

* class
* confidence
* bounding box

## Tracking

* ID consistency
* trajectory
* dwell

## Rules

* intrusion
* line crossing
* loitering
* abandoned object

## ANPR

* normalization
* confidence
* fuzzy search
* watchlist

## Crowd

* counting
* density
* thresholds

## Integration

```text
AI
→ Kafka
→ FastAPI
→ PostgreSQL
→ UI
```

---

# 84. NO FAKE TESTS

Do not create tests that merely assert:

```text
response.status_code == 200
```

while bypassing all meaningful logic.

Tests must exercise:

```text
business rules
data contracts
authorization
event handling
persistence
error behavior
```

---

# 85. FINAL FILES TO CREATE / UPDATE

Create or update as appropriate:

```text
docs/AI_ARCHITECTURE.md
docs/AI_SETUP.md
docs/AI_DEVELOPMENT.md
docs/AI_MODEL_LICENSE_MATRIX.md
docs/AI_MODEL_BENCHMARK.md
docs/AI_HARDWARE_CAPABILITY.md
docs/AI_TENDER_A_TRACEABILITY.md
docs/AI_TENDER_B_TRACEABILITY.md
docs/ANPR_TENDER_A_VALIDATION.md
docs/FRIGATE_EVALUATION.md
docs/AI_PRIVACY_ARCHITECTURE.md
docs/AI_CHAOS_TEST_REPORT.md
docs/AI_SCALE_TEST_REPORT.md
docs/AI_ARCHITECTURE_DECISION.md
docs/AI_PRINCIPAL_ARCHITECT_REVIEW.md
docs/AI_DEMO_RUNBOOK.md
docs/AI_MASTER_MISSION_REPORT.md
```

---

# 86. FINAL MASTER REPORT

Create:

```text
docs/AI_MASTER_MISSION_REPORT.md
```

with:

# 1. Executive Summary

# 2. Starting State

# 3. Architecture

# 4. AI Components Implemented

# 5. AI Components Prototyped

# 6. Frigate Evaluation

# 7. Models Evaluated

# 8. Models Selected

# 9. Models Rejected

# 10. License Audit

# 11. Hardware Requirements

# 12. Benchmarks

# 13. Kafka Integration

# 14. Backend Integration

# 15. Frontend Integration

# 16. Edge Integration

# 17. Privacy

# 18. Security

# 19. Chaos Testing

# 20. Scale Testing

# 21. Tender A Traceability

# 22. Tender B Traceability

# 23. External Dependencies

# 24. Certification Dependencies

# 25. Known Limitations

# 26. Recommended Next 20 AI Tasks

---

# 87. FINAL STATUS MATRIX

Create a final table:

| Capability             | Software | Model | Runtime | License | Tested | Integrated | Production Candidate |
| ---------------------- | -------- | ----- | ------- | ------- | ------ | ---------- | -------------------- |
| Object Detection       |          |       |         |         |        |            |                      |
| Tracking               |          |       |         |         |        |            |                      |
| ANPR                   |          |       |         |         |        |            |                      |
| Vehicle Classification |          |       |         |         |        |            |                      |
| Vehicle Attributes     |          |       |         |         |        |            |                      |
| Intrusion              |          |       |         |         |        |            |                      |
| Line Crossing          |          |       |         |         |        |            |                      |
| Loitering              |          |       |         |         |        |            |                      |
| Abandoned Object       |          |       |         |         |        |            |                      |
| Fall Detection         |          |       |         |         |        |            |                      |
| People Counting        |          |       |         |         |        |            |                      |
| Queue Analytics        |          |       |         |         |        |            |                      |
| Crowd Density          |          |       |         |         |        |            |                      |
| Forecasting            |          |       |         |         |        |            |                      |
| Face Search            |          |       |         |         |        |            |                      |
| ReID                   |          |       |         |         |        |            |                      |

Use truthful statuses.

---

# 88. CRITICAL RULES

## Do NOT

* buy a commercial license
* assume open-source code means open model weights
* integrate research-only weights into production
* expose proprietary cloud APIs
* train giant models unnecessarily
* place inference loops inside FastAPI
* make AI mandatory for recording
* make recording depend on AI
* claim tender certification without evidence
* claim accuracy without benchmark data
* claim production readiness from a demo
* fabricate datasets
* fabricate model performance
* fabricate GPU capacity
* expose biometric information unnecessarily

## DO

* prefer genuinely reusable open-source components
* verify licenses
* benchmark actual models
* use modular adapters
* use Kafka for event integration
* preserve MediaMTX as the video backbone unless evidence demonstrates otherwise
* consider Frigate for general object-detection/event primitives
* use specialized engines for specialized tasks
* isolate AI failures
* maintain versioned event contracts
* maintain model checksums
* document every assumption
* distinguish prototype from production
* test the actual pipeline

---

# 89. MOST IMPORTANT DESIGN DECISION

Do NOT build:

```text
SARVANETRA = one giant AI application
```

Build:

```text
SARVANETRA
    │
    ├── VMS
    ├── PostgreSQL
    ├── Kafka
    ├── MinIO
    ├── RBAC
    ├── Parking
    ├── ANPR Management
    ├── ICCC
    ├── Alerts
    └── Evidence
          ▲
          │
     AI Event Gateway
          ▲
          │
 ┌────────┼───────────────┐
 │        │       │       │
Frigate  ANPR   Crowd   Face
 │        │       │       │
Detector OCR    Density Embed
 │        │       │       │
 └────────┴───────┴───────┘
```

Each AI engine is replaceable.

The event contract is stable.

SARVANETRA remains independent of the model vendor.

---

# 90. SUCCESS CONDITION

The mission is successful when SARVANETRA has:

```text
1. A functioning modular AI architecture
2. At least one real open-source AI inference path
3. Verified licensing for production candidates
4. Standardized Kafka AI events
5. ANPR management integration
6. Object detection integration
7. Tracking foundation
8. At least one real video analytics workflow
9. AI simulator
10. Benchmark framework
11. Edge/central deployment strategy
12. Failure isolation
13. AI observability
14. Tender traceability
15. Reproducible AI demonstration
```

Not every advanced tender capability must necessarily become production-ready in this mission.

For each capability explicitly state:

```text
PRODUCTION-CANDIDATE
WORKING PROTOTYPE
SIMULATION
INTEGRATION READY
EXTERNAL DEPENDENCY
NOT IMPLEMENTED
```

---

# 91. FINAL ENGINEERING PRINCIPLE

The objective is NOT:

> "Add as many AI models as possible."

The objective is:

> **Build an open-source, legally usable, modular, measurable AI perception layer that turns SARVANETRA into a credible intelligent surveillance platform without compromising the stability of the core VMS.**

Use actual experiments.

Use actual benchmarks.

Use actual licensing evidence.

Use actual integration tests.

If a model is unsuitable, reject it.

If a requirement needs an external certified product, say so.

If a prototype works but is not production-ready, say so.

Do not optimize the report for appearance.

Optimize the system for:

**working software + reproducible inference + clean event contracts + legal deployability + tender traceability + maintainability.**

BEGIN THE AUTONOMOUS AI ENGINEERING MISSION.
