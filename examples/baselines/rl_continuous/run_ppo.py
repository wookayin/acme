# Copyright 2018 DeepMind Technologies Limited. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Example running PPO on continuous control tasks."""

from absl import flags
from acme.agents.jax import ppo
import helpers
from absl import app
from acme.utils import lp_utils
from acme.jax import experiments
import launchpad as lp

FLAGS = flags.FLAGS

flags.DEFINE_bool(
    'run_distributed', False, 'Should an agent be executed in a '
    'distributed way (the default is a single-threaded agent)')
flags.DEFINE_string('env_name', 'gym:HalfCheetah-v2', 'What environment to run')
flags.DEFINE_integer('seed', 0, 'Random seed.')
flags.DEFINE_integer('num_steps', 1_000_000, 'Number of env steps to run.')
flags.DEFINE_integer('eval_every', 50_000, 'How often to run evaluation.')


def build_experiment_config():
  """Builds PPO experiment config which can be executed in different ways."""
  # Create an environment, grab the spec, and use it to create networks.
  suite, task = FLAGS.env_name.split(':', 1)

  config = ppo.PPOConfig(entropy_cost=0, learning_rate=1e-4)
  ppo_builder = ppo.PPOBuilder(config)

  layer_sizes = (256, 256, 256)
  make_eval_policy = lambda network: ppo.make_inference_fn(network, True)
  return experiments.Config(
      builder=ppo_builder,
      environment_factory=lambda seed: helpers.make_environment(suite, task),
      network_factory=lambda spec: ppo.make_networks(spec, layer_sizes),
      policy_network_factory=ppo.make_inference_fn,
      eval_policy_network_factory=make_eval_policy,
      seed=FLAGS.seed,
      max_number_of_steps=FLAGS.num_steps)


def main(_):
  config = build_experiment_config()
  if FLAGS.run_distributed:
    program = experiments.make_distributed_experiment(
        experiment=config, num_actors=4)
    lp.launch(program, xm_resources=lp_utils.make_xm_docker_resources(program))
  else:
    experiments.run_experiment(
        experiment=config, eval_every=FLAGS.eval_every, num_eval_episodes=10)


if __name__ == '__main__':
  app.run(main)
