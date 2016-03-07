require 'yaml'
require 'json'
require 'net/http'

class BlueGreen
  def initialize(token, target, config)
    @token = token
    @target = target
    @app_name = config["name"]
    @hooks = config["hooks"] || {}
    @newrelic = config["newrelic"] || {}
    @webhook = config["newrelic"] || {}
  end

  def get_cname
    uri = URI("#{@target}apps/#{@app_name}")
    req = Net::HTTP::Get.new(uri.request_uri, headers)
    res = Net::HTTP.start(uri.hostname, uri.port) { |http| http.request(req) }
    cnames = JSON.parse(res.body)["cname"]
    return cnames if cnames.length > 0
  end

  def remove_cname(cnames)
    uri = URI("#{@target}apps/#{@app_name}/cname")
    req = Net::HTTP::Delete.new(uri.request_uri, headers)
    req.body = {"cname" => cnames}.to_json
    res = Net::HTTP.start(uri.hostname, uri.port) { |http| http.request(req) }
    return res.code.to_i == 200
  end

  def set_cname(cnames)
    uri = URI("#{@target}apps/#{@app_name}/cname")
    req = Net::HTTP::Post.new(uri.request_uri, headers)
    req.body = {"cname" => cnames}.to_json
    res = Net::HTTP.start(uri.hostname, uri.port) { |http| http.request(req) }
    return res.code.to_i == 200
  end

  private
  def headers
    {"Content-Type" => "application/json", "Authorization" => "bearer #{@token}"}
  end
end






