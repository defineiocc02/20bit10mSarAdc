# run: smoke_ramp

- profile: `ideal`
- git: `7a7b49b05a54e6133eb3362a8b4511c0ee842bd3` dirty=True
- seed: 7
- chip: {'n_units': 1024, 'sigma_u': 0.002, 'seed': 7, 'rel_rms': 0.002061573091932644, 'rel_max': 0.007555128360195225}

## 指标

```json
{
  "kind": "ramp",
  "n": 4096,
  "inl_peak_lsb20": 45.43279342805722,
  "inl_peak_ppm": 43.32808821492883,
  "n_valid": 4096,
  "n_overload": 0
}
```
