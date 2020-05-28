<h1 align="center">Immuni Backend Common</h1>

<div align="center">
<img width="256" height="256" src=".github/logo.png">
</div>

<br />

<div align="center">
    <!-- CoC -->
    <a href="CODE_OF_CONDUCT.md">
      <img src="https://img.shields.io/badge/Contributor%20Covenant-v2.0%20adopted-ff69b4.svg" />
    </a>
    <a href="https://docs.python.org/3/">
      <img alt="Python"
      src="https://img.shields.io/badge/python-3.8-informational">
    </a>
    <a href="https://github.com/psf/black">
      <img alt="Code style: black"
      src="https://img.shields.io/badge/code%20style-black-000000.svg">
    </a>
    <a href="http://mypy-lang.org/">
      <img alt="Checked with mypy"
      src="http://www.mypy-lang.org/static/mypy_badge.svg">
    </a>
    <a href="https://github.com/PyCQA/bandit">
      <img alt="security: bandit"
      src="https://img.shields.io/badge/security-bandit-yellow.svg">
    </a>
</div>

<div align="center">
  <h3>
    </span>
    <a href="https://github.com/immuni-app/immuni-documentation">
      Documentation
    </a>
    <span> | </span>    
    <a href="CONTRIBUTING.md">
      Contributing
    </a>
  </h3>
</div>

# Table of contents

- [Context](#context)
- [Installation](#installation)
- [Contributing](#contributing)
  - [Contributors](#contributors)
- [Licence](#licence)
  - [Authors / Copyright](#authors--copyright)
  - [Third-party component licences](#third-party-component-licences)
  - [Licence details](#licence-details)


# Context
This repository contains the source code common to all of Immuni's backend services. Before proceeding, we recommend reading their documentation first:

- [App Configuration Service](https://github.com/immuni-app/immuni-backend-app-configuration)
- [OTP Service](https://github.com/immuni-app/immuni-backend-otp)
- [Exposure Ingestion Service](https://github.com/immuni-app/immuni-backend-exposure-ingestion)
- [Exposure Reporting Service](https://github.com/immuni-app/immuni-backend-exposure-reporting)
- [Analytics Service](https://github.com/immuni-app/immuni-backend-analytics)

**Please take the time to read and consider the other repositories in full before digging into the source code or opening an Issue. They contain a lot of details that are fundamental to understanding the source code and this repository's documentation.**

The common logic aims to consistently provide the following:

- The [Sanic](https://pypi.org/project/sanic/) App creation logic
- The [Celery](https://pypi.org/project/celery/) App creation logic
- The [Prometheus](https://prometheus.io/) monitoring logic and common metrics
- The Python packages dependencies, with optional extras
- The Python packages dev-dependencies
- The Dockerfile
- The linters configurations, and a consistent way to invoke them

# Installation

This repository is not meant to be used as a standalone. On the contrary, it assumes the following:

- It is used as a [Git](https://git-scm.com/) submodule of any of the various Immuni backend services
- The folder containing the submodule is named _common_

To leverage the common logic in any of Immuni’s backend services, the following is added into their _pyproject.toml_:

```toml
[tool.poetry.dependencies]
immuni-common = { path = "common", develop = true, extras = ["aioredis", "celery"] }

[tool.poetry.dev-dependencies]
immuni-common-dev = { path = "common/dev", develop = true }

[tool.poetry.scripts]
checks = "common.scripts:checks"
```

The specific Immuni backend service specifies any extras that it requires to run.

For more information about how the project is generated and structured, please refer to the [Contributing](#contributing) section below.

# Contributing
Contributions are most welcome. Before proceeding, please read the [Code of Conduct](./CODE_OF_CONDUCT.md) for guidance on how to approach the community and create a positive environment. Additionally, please read our [CONTRIBUTING](./CONTRIBUTING.md) file, which contains guidance on ensuring a smooth contribution process.

The Immuni project is composed of different repositories—one for each component or service. Please use this repository for contributions strictly relevant to Immuni's backend services. To propose a feature request, please open an issue in the [Documentation repository](https://github.com/immuni-app/immuni-documentation). This lets everyone involved see it, consider it, and participate in the discussion. Opening an issue or pull request in this repository may slow down the overall process.

## Contributors
Here is a list of Immuni's contributors. Thank you to everyone involved for improving Immuni, day by day.

<a href="https://github.com/immuni-app/immuni-backend-common/graphs/contributors">
  <img
  src="https://contributors-img.web.app/image?repo=immuni-app/immuni-backend-common"
  />
</a>

# Licence

## Authors / Copyright

Copyright 2020 (c) Presidenza del Consiglio dei Ministri.

Please check the [AUTHORS](AUTHORS) file for extended reference.

## Third-party component licences

Please see the Technology Description’s [Backend Services Technologies](https://github.com/immuni-app/documentation/blob/master/Technology%20Description.md#backend-services-technologies) section, which also lists the corresponding licences.

## Licence details

The licence for this repository is a [GNU Affero General Public Licence version 3](https://www.gnu.org/licenses/agpl-3.0.html) (SPDX: AGPL-3.0). Please see the [LICENSE](LICENSE) file for full reference.
