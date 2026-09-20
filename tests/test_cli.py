from click.testing import CliRunner

from scvp.cli.main import cli


def test_cli_lists_runtime_providers_and_plugins():
    runner = CliRunner()

    model = runner.invoke(cli, ["model", "list"])
    search = runner.invoke(cli, ["search"])
    plugins = runner.invoke(cli, ["plugin", "list"])

    assert model.exit_code == 0
    assert "mock" in model.output
    assert search.exit_code == 0
    assert "in_memory" in search.output
    assert plugins.exit_code == 0


def test_cli_runs_agent_and_reads_config():
    runner = CliRunner()

    agent = runner.invoke(cli, ["agent", "run", "hello"])
    config = runner.invoke(cli, ["config", "--key", "model.provider"])

    assert agent.exit_code == 0
    assert "mock" in agent.output
    assert config.exit_code == 0
    assert config.output.strip() == "mock"