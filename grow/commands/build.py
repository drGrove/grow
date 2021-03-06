"""Command for building pods into static deployments."""

import os
import click
from grow.common import utils
from grow.deployments import stats
from grow.deployments.destinations import local as local_destination
from grow.pods import pods
from grow.pods import storage


@click.command()
@click.argument('pod_path', default='.')
@click.option('--out_dir', help='Where to output built files.')
@click.option('--preprocess/--no-preprocess', '-p/-np',
              default=True, is_flag=True,
              help='Whether to run preprocessors.')
@click.option('--clear_cache',
              default=False, is_flag=True,
              help='Clear the pod cache before building.')
@click.option('--file', '--pod-path', 'pod_paths', help='Build only pages affected by content files.', multiple=True)
@click.option('--locate-untranslated',
              default=False, is_flag=True,
              help='Shows untranslated message information.')
def build(pod_path, out_dir, preprocess, clear_cache, pod_paths, locate_untranslated):
    """Generates static files and dumps them to a local destination."""
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    out_dir = out_dir or os.path.join(root, 'build')
    pod = pods.Pod(root, storage=storage.FileStorage)
    if clear_cache:
        pod.podcache.reset(force=True)
    if preprocess:
        pod.preprocess()
    if locate_untranslated:
        pod.enable(pod.FEATURE_TRANSLATION_STATS)
    try:
        config = local_destination.Config(out_dir=out_dir)
        destination = local_destination.LocalDestination(config)
        paths_to_contents = destination.dump(pod, pod_paths=pod_paths)
        repo = utils.get_git_repo(pod.root)
        stats_obj = stats.Stats(pod, paths_to_contents=paths_to_contents)
        destination.deploy(paths_to_contents, stats=stats_obj, repo=repo, confirm=False,
                           test=False, is_partial=bool(pod_paths))
        pod.podcache.write()
    except pods.Error as e:
        raise click.ClickException(str(e))
    if locate_untranslated:
        pod.translation_stats.pretty_print()
