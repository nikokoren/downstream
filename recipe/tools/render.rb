# Renders one view with Ruby Liquid, the engine TRMNL runs (liquidjs, used before, accepted a
# `}` inside `{{ }}` that Ruby Liquid rejects; the author saw the error on a device, 2026-09-30).
#
# Usage: ruby render.rb <view> < context.json   → HTML on stdout; errors on stderr, exit 1.
# As on TRMNL, Shared is prepended to the view and its `{% template name %}` blocks become
# partials for `{% render "name" %}`. Needs the liquid gem (`gem install liquid`).
Encoding.default_external = Encoding::UTF_8
require "json"
require "liquid"

src = File.expand_path("../src", __dir__)
view = ARGV.fetch(0)
partials = {}
shared = File.read(File.join(src, "shared.liquid")).gsub(
  /\{%-?\s*template\s+(\w+)\s*-?%\}(.*?)\{%-?\s*endtemplate\s*-?%\}/m
) { partials[Regexp.last_match(1)] = Regexp.last_match(2); "" }

# Partials by name, as TRMNL's `{% template %}` provides them.
class Partials
  def initialize(h) = @h = h
  def read_template_file(name) = @h.fetch(name) { raise Liquid::FileSystemError, "no template #{name}" }
end

env = Liquid::Environment.build { |e| e.file_system = Partials.new(partials) }
template = Liquid::Template.parse(shared + File.read(File.join(src, "#{view}.liquid")),
                                  environment: env, error_mode: :strict)
html = template.render!(JSON.parse($stdin.read), strict_filters: true)
print html
