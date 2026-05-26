# Adaptive ML Stability Runtime Notes

## Purpose

Adaptive ML Stability Runtime is a future governance hook for ML training stability. It monitors training behavior and applies controlled governance actions before `optimizer.step`.

This is not part of Live Case Loop, Operator Review, ACPC PV diagnostics, EMS/PV/BESS control, or production live operations.

## Correct Execution Order

```python
runtime = AdaptiveStabilityRuntime(...)
hook = GovernanceHook(runtime, optimizer, model)

for batch_X, batch_y in dataloader:
    optimizer.zero_grad()

    output = model(batch_X)
    loss = criterion(output, batch_y)

    loss.backward()

    governance_result = hook.execute(loss.item())

    optimizer.step()
```

## Critical Rule

`GovernanceHook` must be called after `loss.backward()`, because gradients exist only after backward propagation.

Gradient clipping before `backward()` is wrong.

## REDUCE_LR Policy

```python
if action == GovernanceAction.REDUCE_LR:
    factor = max(0.1, min(0.8, 0.5 + 0.3 * confidence))

    for group in self.optimizer.param_groups:
        old_lr = group["lr"]
        group["lr"] *= factor
        logger.info(
            f"REDUCE_LR | {old_lr} -> {group['lr']} | confidence={confidence:.4f}"
        )
```

## ENTER_RECOVERY Policy

```python
elif action == GovernanceAction.ENTER_RECOVERY:
    for group in self.optimizer.param_groups:
        group["lr"] *= 0.25

    self.recovery_mode = True
    logger.warning("ENTER_RECOVERY")
```

## ENABLE_GRAD_CLIPPING Policy

```python
elif action == GovernanceAction.ENABLE_GRAD_CLIPPING:
    torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.max_norm)
```

## Governance Safety Notes

- LR factor must have a lower bound.
- Hook must not execute clipping before `backward()`.
- `ENTER_RECOVERY` must set `recovery_mode`.
- Governance must not execute autonomous actions outside ML training scope.
- This is a future module, not live production control.

## Integration Boundary

At this stage:

- do not implement in `app/live_ops`,
- do not connect to Operator Review,
- do not connect to ACPC PV diagnostics,
- do not connect to EMS/PV/BESS,
- do not execute real emergency stop outside simulation/training loop.
