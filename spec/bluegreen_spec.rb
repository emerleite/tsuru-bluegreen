require 'spec_helper'

describe BlueGreen do
  let :config do
    {
      'name' => 'xpto',
      'hooks' => {'before_pre'  => 'echo test', 'after_swap'  => 'undefined_command'},
      'newrelic' => {'api_key'  => 'some-api-key', 'app_id'  => '123'},
      'webhook' => {'endpoint' => 'http://example.com', 'payload_extras' => 'key1=value1&key2=value2'}
    }
  end

  let :target do
    "http://tsuru.globoi.com/1.0/"
  end

  let :token do
    "token"
  end

  let :headers do
    {"Content-Type" => "application/json", "Authorization" => "bearer #{token}"}
  end

  subject do
    BlueGreen.new token, target, config
  end

  describe "#get_cname" do
    it "should return a list when present" do
      stub_request(:get, "#{target}apps/xpto")
        .with(headers: headers)
        .to_return(body: '{"cname":["cname1", "cname2"]}')
      expect(subject.get_cname).to eql ["cname1", "cname2"]
    end

    it "should return nil when cname list is empty" do
      stub_request(:get, "#{target}apps/xpto")
        .with(headers: headers)
        .to_return(body: '{"cname":[]}')
      expect(subject.get_cname).to be_nil
    end
  end

  describe "#remove_cname" do
    let :cnames do
      {"cname" => ["cname1", "cname2"]}
    end
    
    it "should return true when can remove" do
      stub_request(:delete, "#{target}apps/xpto/cname")
        .with(body: cnames.to_json, headers: headers)
        .to_return(status: 200, body: "")
      expect(subject.remove_cname(["cname1", "cname2"])).to be_truthy
    end

    it "should return false when can't remove" do
      stub_request(:delete, "#{target}apps/xpto/cname")
        .with(body: cnames.to_json, headers: headers)
        .to_return(status: 500, body: "")
      expect(subject.remove_cname(["cname1", "cname2"])).to be_falsy
    end
  end
end
