# DevSecOps & CI/CD Pipeline Architecture: OptiSchedule UMB

## 1. Overview
The OptiSchedule UMB engineering workflow incorporates automated CI/CD, Static Application Security Testing (SAST), Code Quality Gates, and Mutation Testing. Every push and pull request targeted at the `main` branch undergoes automated validation.

---

## 2. GitHub Workflows Architecture

### 2.1. Continuous Integration & Quality Gate (`.github/workflows/ci.yml`)
- **Environment:** Ubuntu Linux (`ubuntu-latest`) with headless X11/Qt runtime packages (`libegl1`, `libgl1`, `libxkbcommon-x11-0`, `xvfb`, etc.).
- **Headless Display Emulation:** `QT_QPA_PLATFORM=offscreen` ensures that PySide6/Qt widgets execute tests and calculations without attempting to initialize a physical display server.
- **Automated Test Suite:**
  ```bash
  pytest tests/ --cov=app --cov-report=xml:coverage.xml --cov-report=term -v
  ```
  Generates machine-readable coverage reports (`coverage.xml`) with a total line coverage of **63%** across the application.
- **Mutation Testing Gate:**
  ```bash
  python scripts/run_mutation_tests.py --threshold 50
  ```
  Executes `mutmut` over critical optimization and security logic. Fails the build if the Mutation Score drops below 50%.
- **SonarCloud Analysis:**
  Integrates `SonarSource/sonarcloud-github-action@master` consuming `sonar-project.properties` and `coverage.xml`.

### 2.2. Automated Dependency Auditing: Dependabot (`.github/dependabot.yml`)
- Audits `pip` packages in `/` on a weekly schedule.
- Audits GitHub Actions workflow action versions (`actions/checkout`, `actions/setup-python`) on a weekly schedule.
- Operates natively and securely on private repositories without requiring enterprise licensing.

---

## 3. Static Code Analysis Configuration (`sonar-project.properties`)
- **Project Key:** `vranfe_optischedule`
- **Organization:** `vranfe`
- **Sources Monitored:** `app/`
- **Tests Monitored:** `tests/`
- **Coverage Path:** `coverage.xml`
- **Python Versions:** 3.11, 3.12, 3.13, 3.14

---

## 4. Local vs Cloud Verification
- **Local:** Run `pytest tests/ --cov=app --cov-report=term` to inspect code coverage.
- **Cloud:** Pushing to GitHub triggers the Actions tab, runs test suites, checks mutation scores, and posts the status to README badges.
