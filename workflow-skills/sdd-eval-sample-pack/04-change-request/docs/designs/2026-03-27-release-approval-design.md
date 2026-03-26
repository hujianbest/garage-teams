# Release Approval Implementation Design

Status: Approved

## Overview

Use a simple approval service and notification service.

## Architecture

- Request lifecycle module
- Manager approval module
- Applicant notification module

## Interfaces And Contracts

- Submit request
- Approve request
- Notify applicant

## Testing Strategy

- TDD for request approval lifecycle
- Verification of approval notification behavior
