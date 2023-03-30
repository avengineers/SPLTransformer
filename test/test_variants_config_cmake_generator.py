from transformer import VariantConfigCMakeGenerator


def test_to_string():
    generator = VariantConfigCMakeGenerator()
    assert "" == generator.to_string()
