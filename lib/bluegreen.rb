require 'yaml'
require 'json'
require 'net/http'
require 'debugger'

class BlueGreen
  def initialize(token, target, config)
    @token = token
    @target = target
    @app_name = config["name"]
    @hooks = config["hooks"] || {}
    @newrelic = config["newrelic"] || {}
    @webhook = config["newrelic"] || {}
  end

  def get_cname(app)
    uri = URI("#{@target}apps/#{app}")
    req = Net::HTTP::Get.new(uri.request_uri, headers)
    res = Net::HTTP.start(uri.hostname, uri.port) { |http| http.request(req) }
    cnames = JSON.parse(res.body)["cname"]
    return cnames if cnames.length > 0
  end

  def remove_cname(app, cnames)
    uri = URI("#{@target}apps/#{app}/cname")
    req = Net::HTTP::Delete.new(uri.request_uri, headers)
    req.body = {"cname" => cnames}.to_json
    res = Net::HTTP.start(uri.hostname, uri.port) { |http| http.request(req) }
    return res.code.to_i == 200
  end

  def set_cname(app, cnames)
    uri = URI("#{@target}apps/#{app}/cname")
    req = Net::HTTP::Post.new(uri.request_uri, headers)
    req.body = {"cname" => cnames}.to_json
    res = Net::HTTP.start(uri.hostname, uri.port) { |http| http.request(req) }
    return res.code.to_i == 200
  end

  def env_set(app, key, value)
    uri = URI("#{@target}apps/#{app}/env?noRestart=true")
    req = Net::HTTP::Post.new(uri.request_uri, headers)
    req.body = {key => value}.to_json
    res = Net::HTTP.start(uri.hostname, uri.port) { |http| http.request(req) }
    return res.code.to_i == 200
  end

  def env_get(app, key)
    uri = URI("#{@target}apps/#{app}/env")
    req = Net::HTTP::Get.new(uri.request_uri, headers)
    req.body = [key].to_json
    res = Net::HTTP.start(uri.hostname, uri.port) { |http| http.request(req) }
    return if res.body === "null"

    values = JSON.parse(res.body)
    values[0]["value"] if values.length > 0
  end

  def total_units(app)
    uri = URI("#{@target}apps/#{app}")
    req = Net::HTTP::Get.new(uri.request_uri, headers)
    res = Net::HTTP.start(uri.hostname, uri.port) { |http| http.request(req) }
    units = JSON.parse(res.body)["units"]
    process_count = {}
    units.map do |unit|
      process_name = unit["ProcessName"]
      process_count[process_name] ? process_count[process_name] += 1 : process_count[process_name] = 1
    end
    process_count
  end

  def remove_units(app, units_to_keep=0)
    total_units = total_units(app)
    results = total_units.map do |process_name, units|
      remove_units_per_process_type(app, units - units_to_keep, process_name)
    end

    results.all?
  end

  def add_units(app, total_units_after_add)
    total_units = total_units(app)

    results = total_units_after_add.map do |process_name, units|
      units_to_add = 0

      if total_units[process_name]
        units_to_add = units - total_units[process_name]
      else
        units_to_add = units
      end

     add_units_per_process_type(app, units_to_add, units, process_name) if units_to_add > 0
    end

    results.compact.all?
  end

  private

  def add_units_per_process_type(app, units_to_add, total_units_after_add, process_name)
    uri = URI("#{@target}apps/#{app}/units?units=#{units_to_add}&process=#{process_name}")
    req = Net::HTTP::Put.new(uri.request_uri, headers)
    res = Net::HTTP.start(uri.hostname, uri.port) { |http| http.request(req) }

    if (res.code.to_i != 200) || (total_units(app)[process_name] != total_units_after_add)
      puts "Error adding '#{units_to_add}' units to #{process_name} process in #{app}. Aborting..."
      return false
    end

    return true
  end

  def remove_units_per_process_type(app, units_to_remove, process_name)
    uri = URI("#{@target}apps/#{app}/units?units=#{units_to_remove}&process=#{process_name}")
    req = Net::HTTP::Delete.new(uri.request_uri, headers.merge({"Content-Type" => "application/x-www-form-urlencoded"}))
    res = Net::HTTP.start(uri.hostname, uri.port) { |http| http.request(req) }

    if res.code.to_i != 200
      puts "Error removing '#{process_name}' units from #{app}. You'll need to remove manually."
      return false
    end

    return true
  end

  def headers
    {"Content-Type" => "application/json", "Authorization" => "bearer #{@token}"}
  end
end

