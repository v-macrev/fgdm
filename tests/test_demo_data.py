from fgdm.application.demo_data import DemoDatasetConfig, generate_demo_dataset


def test_demo_dataset_generation():
    cfg = DemoDatasetConfig(n_keys=3, n_days=20)
    rows = generate_demo_dataset(cfg)
    assert len(rows) == 60
    assert rows[0].cd_key.startswith("SKU_")